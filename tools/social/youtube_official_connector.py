"""YouTube Data API v3 的 V1 最小只读客户端。"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

import httpx

from tools.social.youtube_p0_v1 import evaluate_v1_preflight


OFFICIAL_BASE_URL = "https://www.googleapis.com/youtube/v3"
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

_COVERAGE_BY_REASON = {
    "commentsDisabled": "comments_disabled",
    "videoNotFound": "video_unavailable",
    "forbidden": "permission_denied",
    "channelForbidden": "permission_denied",
    "quotaExceeded": "quota_exhausted",
    "dailyLimitExceeded": "quota_exhausted",
    "backendError": "transient_error",
    "internalError": "transient_error",
    "processingFailure": "transient_error",
}


class YouTubeDataApiError(RuntimeError):
    """不包含凭证和原始响应正文的结构化 API 错误。"""

    def __init__(
        self,
        *,
        endpoint: str,
        status_code: int,
        reason: str,
        coverage_status: str | None,
    ) -> None:
        self.endpoint = endpoint
        self.status_code = status_code
        self.reason = reason
        self.coverage_status = coverage_status
        super().__init__(f"{endpoint} failed: HTTP {status_code} ({reason})")

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "reason": self.reason,
            "coverage_status": self.coverage_status,
        }


class YouTubeOfficialClient:
    """仅实现 V1 smoke 所需的四个官方只读端点。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = OFFICIAL_BASE_URL,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        normalized_base_url = base_url.rstrip("/")
        parsed = urlparse(normalized_base_url)
        if normalized_base_url != OFFICIAL_BASE_URL and parsed.hostname not in _LOOPBACK_HOSTS:
            raise ValueError("base_url must be the official API or a loopback test server")
        self._api_key = api_key
        self._base_url = normalized_base_url
        self._client = httpx.Client(
            timeout=timeout_seconds,
            trust_env=parsed.hostname not in _LOOPBACK_HOSTS,
        )

    def __enter__(self) -> "YouTubeOfficialClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def validate_access(self, channel_id: str) -> dict[str, Any]:
        channel_id = _required_id(channel_id, "channel_id")
        response = self._get(
            "channels",
            "channels.list",
            {
                "part": "id,contentDetails",
                "id": channel_id,
                "maxResults": 1,
            },
        )
        items = response["items"]
        if not items:
            raise YouTubeDataApiError(
                endpoint="channels.list",
                status_code=404,
                reason="channelNotFound",
                coverage_status=None,
            )
        uploads = (
            items[0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )
        if not isinstance(uploads, str) or not uploads:
            raise YouTubeDataApiError(
                endpoint="channels.list",
                status_code=200,
                reason="schemaMismatch",
                coverage_status="schema_mismatch",
            )
        return {
            "status": "PASS",
            "endpoint": "channels.list",
            "channel_id": items[0].get("id"),
            "uploads_playlist_id": uploads,
            "request": response["request"],
        }

    def fetch_video(self, video_id: str) -> dict[str, Any]:
        video_id = _required_id(video_id, "video_id")
        response = self._get(
            "videos",
            "videos.list",
            {
                "part": "snippet,status,statistics",
                "id": video_id,
            },
        )
        if not response["items"]:
            raise YouTubeDataApiError(
                endpoint="videos.list",
                status_code=404,
                reason="videoNotFound",
                coverage_status="video_unavailable",
            )
        return {
            "status": "PASS",
            "endpoint": "videos.list",
            "item": response["items"][0],
            "request": response["request"],
        }

    def fetch_comment_threads(
        self,
        video_id: str,
        *,
        cursor: str | None = None,
        max_results: int = 100,
    ) -> dict[str, Any]:
        video_id = _required_id(video_id, "video_id")
        _validate_page_size(max_results)
        params: dict[str, Any] = {
            "part": "id,snippet,replies",
            "videoId": video_id,
            "order": "time",
            "textFormat": "plainText",
            "maxResults": max_results,
        }
        if cursor:
            params["pageToken"] = cursor
        response = self._get("commentThreads", "commentThreads.list", params)
        return _page_result("commentThreads.list", response)

    def fetch_replies(
        self,
        parent_comment_id: str,
        *,
        cursor: str | None = None,
        max_results: int = 100,
    ) -> dict[str, Any]:
        parent_comment_id = _required_id(parent_comment_id, "parent_comment_id")
        _validate_page_size(max_results)
        params: dict[str, Any] = {
            "part": "id,snippet",
            "parentId": parent_comment_id,
            "textFormat": "plainText",
            "maxResults": max_results,
        }
        if cursor:
            params["pageToken"] = cursor
        response = self._get("comments", "comments.list", params)
        return _page_result("comments.list", response)

    def _get(
        self,
        resource: str,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            response = self._client.get(
                f"{self._base_url}/{resource}",
                params=params,
                headers={
                    "Accept": "application/json",
                    "X-Goog-Api-Key": self._api_key,
                },
            )
        except httpx.RequestError as exc:
            raise YouTubeDataApiError(
                endpoint=endpoint,
                status_code=0,
                reason="transportError",
                coverage_status="transient_error",
            ) from exc
        payload = _response_json(response, endpoint)
        if response.status_code >= 400:
            reason = _error_reason(payload)
            raise YouTubeDataApiError(
                endpoint=endpoint,
                status_code=response.status_code,
                reason=reason,
                coverage_status=_coverage_status(response.status_code, reason),
            )
        items = payload.get("items")
        if not isinstance(items, list):
            raise YouTubeDataApiError(
                endpoint=endpoint,
                status_code=response.status_code,
                reason="schemaMismatch",
                coverage_status="schema_mismatch",
            )
        return {
            "items": items,
            "nextPageToken": payload.get("nextPageToken"),
            "request": {"endpoint": endpoint, "params": dict(params)},
        }


def run_v1_readonly_smoke(
    record: dict[str, Any],
    *,
    environ: Mapping[str, str],
    client: YouTubeOfficialClient,
) -> dict[str, Any]:
    """在 preflight 通过后运行四端点 smoke，并只返回脱敏证据摘要。"""
    preflight = evaluate_v1_preflight(record, environ=environ)
    report: dict[str, Any] = {
        **preflight,
        "live_request_attempted": False,
        "evidence_level": "readonly_smoke",
    }
    if not preflight["live_request_allowed"]:
        return report

    samples = record["samples"]
    report["live_request_attempted"] = True
    try:
        access = client.validate_access(samples["channel_id"])
        video = client.fetch_video(samples["video_id"])
        threads = client.fetch_comment_threads(samples["video_id"])
        replies = client.fetch_replies(samples["reply_parent_id"])
    except YouTubeDataApiError as exc:
        report["overall_status"] = "NO_GO"
        report["error"] = exc.to_dict()
        return report

    validation_error = _validate_smoke_relationships(
        samples=samples,
        access=access,
        video=video,
        threads=threads,
        replies=replies,
    )
    if validation_error is not None:
        report["overall_status"] = "NO_GO"
        report["error"] = validation_error
        return report

    report["overall_status"] = "PASS"
    report["evidence"] = {
        "access": {
            "channel_id": access["channel_id"],
            "uploads_playlist_id_present": bool(access["uploads_playlist_id"]),
        },
        "video": {
            "video_id": video["item"]["id"],
            "channel_id": video["item"]["snippet"]["channelId"],
        },
        "comment_threads": {
            "items_count": len(threads["items"]),
            "next_page_token_present": bool(threads["next_page_token"]),
        },
        "replies": {
            "items_count": len(replies["items"]),
            "next_page_token_present": bool(replies["next_page_token"]),
        },
    }
    return report


def _validate_smoke_relationships(
    *,
    samples: dict[str, str],
    access: dict[str, Any],
    video: dict[str, Any],
    threads: dict[str, Any],
    replies: dict[str, Any],
) -> dict[str, Any] | None:
    video_item = video["item"]
    if access["channel_id"] != samples["channel_id"]:
        return _smoke_schema_error("channel_id_mismatch")
    if video_item.get("id") != samples["video_id"]:
        return _smoke_schema_error("video_id_mismatch")
    snippet = video_item.get("snippet")
    if not isinstance(snippet, dict) or snippet.get("channelId") != samples["channel_id"]:
        return _smoke_schema_error("video_channel_mismatch")
    if not threads["items"]:
        return {
            "reason": "noCommentThreads",
            "coverage_status": "zero_comments_confirmed",
        }

    top_level_ids: set[str] = set()
    for thread in threads["items"]:
        if not isinstance(thread, dict):
            return _smoke_schema_error("thread_schema_mismatch")
        thread_snippet = thread.get("snippet")
        if not isinstance(thread_snippet, dict):
            return _smoke_schema_error("thread_schema_mismatch")
        if thread_snippet.get("videoId") != samples["video_id"]:
            return _smoke_schema_error("thread_video_mismatch")
        top_comment = thread_snippet.get("topLevelComment")
        if isinstance(top_comment, dict) and isinstance(top_comment.get("id"), str):
            top_level_ids.add(top_comment["id"])
    if samples["reply_parent_id"] not in top_level_ids:
        return _smoke_schema_error("reply_parent_not_in_thread_page")
    if not replies["items"]:
        return _smoke_schema_error("no_replies_for_approved_parent")
    for reply in replies["items"]:
        if not isinstance(reply, dict):
            return _smoke_schema_error("reply_schema_mismatch")
        reply_snippet = reply.get("snippet")
        if (
            not isinstance(reply_snippet, dict)
            or reply_snippet.get("parentId") != samples["reply_parent_id"]
        ):
            return _smoke_schema_error("reply_parent_mismatch")
    return None


def _smoke_schema_error(reason: str) -> dict[str, Any]:
    return {"reason": reason, "coverage_status": "schema_mismatch"}


def _page_result(endpoint: str, response: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "endpoint": endpoint,
        "items": response["items"],
        "next_page_token": response.get("nextPageToken"),
        "request": response["request"],
    }


def _response_json(response: httpx.Response, endpoint: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise YouTubeDataApiError(
            endpoint=endpoint,
            status_code=response.status_code,
            reason="schemaMismatch",
            coverage_status="schema_mismatch",
        ) from exc
    if not isinstance(payload, dict):
        raise YouTubeDataApiError(
            endpoint=endpoint,
            status_code=response.status_code,
            reason="schemaMismatch",
            coverage_status="schema_mismatch",
        )
    return payload


def _error_reason(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    if not isinstance(error, dict):
        return "unknownError"
    errors = error.get("errors")
    if isinstance(errors, list) and errors and isinstance(errors[0], dict):
        reason = errors[0].get("reason")
        if isinstance(reason, str) and reason:
            return reason
    return "unknownError"


def _coverage_status(status_code: int, reason: str) -> str | None:
    if reason in _COVERAGE_BY_REASON:
        return _COVERAGE_BY_REASON[reason]
    if status_code == 429:
        return "quota_exhausted"
    if status_code >= 500:
        return "transient_error"
    if status_code == 403:
        return "permission_denied"
    if status_code == 404:
        return None
    return "transient_error"


def _required_id(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _validate_page_size(max_results: int) -> None:
    if not isinstance(max_results, int) or not 1 <= max_results <= 100:
        raise ValueError("max_results must be between 1 and 100")
