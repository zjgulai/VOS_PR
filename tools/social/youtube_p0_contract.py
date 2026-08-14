"""YouTube P0 的纯离线数据契约与 V0 fixture 处理。"""
from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_SCOPE_KEYS = {
    "scope_id",
    "scope_version",
    "workspace_id",
    "provider",
    "strategy",
    "use_case",
    "products",
    "regions",
    "languages",
    "approved_channel_ids",
    "queries",
    "status",
}

REQUIRED_COVERAGE_STATUSES = {
    "complete_for_defined_scope",
    "partial_page_cap",
    "comments_disabled",
    "made_for_kids_no_comments",
    "video_unavailable",
    "permission_denied",
    "quota_exhausted",
    "transient_error",
    "schema_mismatch",
    "zero_comments_confirmed",
}


def validate_source_scope(scope: dict[str, Any]) -> list[str]:
    """返回 SourceScope 的 V0 契约错误；空列表表示 fixture 可解析。"""
    errors: list[str] = []
    missing = sorted(REQUIRED_SCOPE_KEYS - scope.keys())
    if missing:
        errors.append(f"missing keys: {', '.join(missing)}")

    if scope.get("provider") != "youtube_data_api":
        errors.append("provider must be youtube_data_api")
    if scope.get("strategy") != "official_api":
        errors.append("strategy must be official_api")

    for key in ("scope_id", "scope_version", "workspace_id", "use_case", "status"):
        if not isinstance(scope.get(key), str) or not scope[key].strip():
            errors.append(f"{key} must be a non-empty string")

    for key in ("products", "regions", "languages", "approved_channel_ids", "queries"):
        value = scope.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"{key} must be a non-empty list")

    for index, product in enumerate(scope.get("products", [])):
        if not isinstance(product, dict) or not product.get("standard_model"):
            errors.append(f"products[{index}].standard_model is required")
        aliases = product.get("aliases") if isinstance(product, dict) else None
        if not isinstance(aliases, list):
            errors.append(f"products[{index}].aliases must be a list")

    return errors


def normalize_fixture_comments(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    """把合成 commentThread/reply 页标准化，并按 comment ID 去重。"""
    collection = fixture["collection"]
    video_id = collection["video_id"]
    channel_id = collection["channel_id"]
    seen: dict[str, dict[str, Any]] = {}

    def add_record(record: dict[str, Any]) -> None:
        comment_id = record["comment_id"]
        existing = seen.get(comment_id)
        if existing is not None and existing != record:
            raise ValueError(f"conflicting duplicate comment: {comment_id}")
        seen.setdefault(comment_id, record)

    for page in fixture.get("comment_thread_pages", []):
        for thread in page.get("items", []):
            thread_id = _required_string(thread, "id")
            thread_snippet = _required_dict(thread, "snippet")
            if thread_snippet.get("videoId") != video_id:
                raise ValueError(f"thread {thread_id} has unexpected videoId")
            top_comment = _required_dict(thread_snippet, "topLevelComment")
            top_comment_id = _required_string(top_comment, "id")
            total_reply_count = int(thread_snippet.get("totalReplyCount", 0))
            add_record(
                _normalize_comment(
                    top_comment,
                    collection=collection,
                    video_id=video_id,
                    channel_id=channel_id,
                    thread_id=thread_id,
                    parent_comment_id=None,
                    reply_count=total_reply_count,
                )
            )

            embedded_replies = thread.get("replies", {}).get("comments", [])
            reply_pages = fixture.get("reply_pages_by_parent", {}).get(top_comment_id, [])
            all_replies = list(embedded_replies)
            for reply_page in reply_pages:
                all_replies.extend(reply_page.get("items", []))

            for reply in all_replies:
                snippet = _required_dict(reply, "snippet")
                parent_id = _required_string(snippet, "parentId")
                if parent_id != top_comment_id:
                    raise ValueError(
                        f"reply {_required_string(reply, 'id')} has unexpected parentId"
                    )
                add_record(
                    _normalize_comment(
                        reply,
                        collection=collection,
                        video_id=video_id,
                        channel_id=channel_id,
                        thread_id=thread_id,
                        parent_comment_id=parent_id,
                        reply_count=0,
                    )
                )

    return list(seen.values())


def map_coverage_status(
    *,
    items_count: int,
    next_page_token: str | None,
    error_reason: str | None,
    page_cap_reached: bool,
    made_for_kids: bool,
) -> str:
    """把 API/停止条件映射为互斥的 Coverage 状态。"""
    if made_for_kids:
        return "made_for_kids_no_comments"

    error_map = {
        "commentsDisabled": "comments_disabled",
        "videoNotFound": "video_unavailable",
        "forbidden": "permission_denied",
        "quotaExceeded": "quota_exhausted",
        "dailyLimitExceeded": "quota_exhausted",
        "backendError": "transient_error",
        "internalError": "transient_error",
        "schemaMismatch": "schema_mismatch",
    }
    if error_reason:
        return error_map.get(error_reason, "transient_error")
    if page_cap_reached and next_page_token:
        return "partial_page_cap"
    if items_count == 0 and not next_page_token:
        return "zero_comments_confirmed"
    if not next_page_token:
        return "complete_for_defined_scope"
    return "partial_page_cap"


def locate_lifecycle_targets(
    records: list[dict[str, Any]], comment_id: str
) -> dict[str, Any]:
    """按 comment ID 定位原始记录和所有已登记派生对象。"""
    for record in records:
        if record.get("comment_id") == comment_id:
            return {
                "record_id": record["record_id"],
                "raw_object_ref": record["raw_object_ref"],
                "evidence_ids": list(record.get("evidence_ids", [])),
                "insight_ids": list(record.get("insight_ids", [])),
                "action_ids": list(record.get("action_ids", [])),
            }
    raise KeyError(f"comment_id not found: {comment_id}")


def lifecycle_action(record: dict[str, Any], as_of: str) -> str:
    """返回 V0 生命周期 fixture 在指定时间点的预期动作。"""
    if record.get("deletion_requested_at"):
        return "delete_due_to_request"
    if record.get("source_status") == "missing":
        return "mark_source_missing"
    if _parse_timestamp(record["refresh_or_delete_at"]) <= _parse_timestamp(as_of):
        return "refresh_due"
    return "none"


def audit_python_source_text(source: str) -> list[dict[str, Any]]:
    """静态识别个人配置读取、宽泛异常吞没和无证据范围默认值。"""
    tree = ast.parse(source)
    findings: dict[str, set[int]] = {}

    def add(code: str, line: int) -> None:
        findings.setdefault(code, set()).add(line)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            segment = ast.get_source_segment(source, node) or ""
            if any(name in segment for name in (".zshrc", ".bashrc", "shell history")):
                add("personal_profile_read", node.lineno)

        if isinstance(node, ast.ExceptHandler):
            catches_broad = node.type is None or (
                isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"}
            )
            if catches_broad and any(isinstance(statement, ast.Pass) for statement in node.body):
                add("silent_broad_exception", node.lineno)

        assignment: tuple[list[ast.expr], ast.expr | None] | None = None
        if isinstance(node, ast.AnnAssign):
            assignment = ([node.target], node.value)
        elif isinstance(node, ast.Assign):
            assignment = (list(node.targets), node.value)

        if assignment is not None:
            targets, value = assignment
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id == "country_code" and value.value == "US":
                    add("unverified_scope_default", node.lineno)
                if target.id == "language" and value.value == "en":
                    add("unverified_scope_default", node.lineno)
                upper_name = target.id.upper()
                if value.value and any(
                    marker in upper_name
                    for marker in ("API_KEY", "TOKEN", "SECRET", "PASSWORD")
                ):
                    add("hardcoded_secret", node.lineno)

    return [
        {"code": code, "lines": sorted(lines)}
        for code, lines in sorted(findings.items())
    ]


def build_v0_report(
    fixture: dict[str, Any], collector_path: Path
) -> dict[str, Any]:
    """运行六项 V0 离线门并返回机器可读结果。"""
    checks: dict[str, dict[str, Any]] = {}

    scope_errors = validate_source_scope(fixture.get("scope", {}))
    if fixture.get("fixture_only") is not True:
        scope_errors.append("fixture_only must be true for V0")
    checks["source_scope_schema"] = _check_result(
        not scope_errors,
        {"errors": scope_errors},
    )

    try:
        records = normalize_fixture_comments(fixture)
        unique_mentions = len({record["mention_id"] for record in records})
        top_level_count = sum(record["is_top_level"] for record in records)
        reply_count = len(records) - top_level_count
        normalization_ok = (
            bool(records)
            and top_level_count > 0
            and reply_count > 0
            and len(records) == unique_mentions
            and all(
                record["parent_comment_id"] is None or not record["is_top_level"]
                for record in records
            )
        )
        normalization_detail: dict[str, Any] = {
            "records": len(records),
            "unique_mentions": unique_mentions,
            "top_level_records": top_level_count,
            "reply_records": reply_count,
        }
    except (KeyError, TypeError, ValueError) as exc:
        records = []
        normalization_ok = False
        normalization_detail = {"error": str(exc)}
    checks["comment_thread_reply_normalization"] = _check_result(
        normalization_ok,
        normalization_detail,
    )

    coverage_cases = fixture.get("coverage_cases", [])
    mismatches: list[dict[str, str]] = []
    for case in coverage_cases:
        actual = map_coverage_status(**case["input"])
        if actual != case["expected"]:
            mismatches.append(
                {"name": case["name"], "expected": case["expected"], "actual": actual}
            )
    declared_statuses = {
        case.get("expected") for case in coverage_cases if isinstance(case, dict)
    }
    missing_statuses = sorted(REQUIRED_COVERAGE_STATUSES - declared_statuses)
    checks["coverage_status_mapping"] = _check_result(
        bool(coverage_cases) and not mismatches and not missing_statuses,
        {
            "cases": len(coverage_cases),
            "mismatches": mismatches,
            "missing_statuses": missing_statuses,
        },
    )

    source = collector_path.read_text(encoding="utf-8")
    audit_findings = audit_python_source_text(source)
    audit_codes = {finding["code"] for finding in audit_findings}
    scope_safety_findings = [
        finding
        for finding in audit_findings
        if finding["code"]
        in {"hardcoded_secret", "personal_profile_read", "unverified_scope_default"}
    ]
    checks["secret_and_profile_safety"] = _check_result(
        not (
            {"hardcoded_secret", "personal_profile_read", "unverified_scope_default"}
            & audit_codes
        ),
        {"findings": scope_safety_findings},
    )
    silent_findings = [
        finding for finding in audit_findings if finding["code"] == "silent_broad_exception"
    ]
    checks["silent_exception_safety"] = _check_result(
        "silent_broad_exception" not in audit_codes,
        {"findings": silent_findings},
    )

    lifecycle_errors: list[str] = []
    lifecycle_actions: dict[str, str] = {}
    for record in fixture.get("lifecycle_records", []):
        comment_id = record["comment_id"]
        try:
            locate_lifecycle_targets(fixture["lifecycle_records"], comment_id)
            lifecycle_actions[comment_id] = lifecycle_action(
                record,
                record["refresh_or_delete_at"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            lifecycle_errors.append(f"{comment_id}: {exc}")
    required_actions = {"refresh_due", "mark_source_missing", "delete_due_to_request"}
    lifecycle_ok = not lifecycle_errors and required_actions.issubset(lifecycle_actions.values())
    checks["lifecycle_locatability"] = _check_result(
        lifecycle_ok,
        {"actions": lifecycle_actions, "errors": lifecycle_errors},
    )

    overall_status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "NO_GO"
    return {
        "fixture_only": bool(fixture.get("fixture_only")),
        "overall_status": overall_status,
        "checks": checks,
        "metrics": {
            "normalized_comments": len(records),
            "coverage_cases": len(fixture.get("coverage_cases", [])),
            "lifecycle_records": len(fixture.get("lifecycle_records", [])),
        },
    }


def _normalize_comment(
    comment: dict[str, Any],
    *,
    collection: dict[str, Any],
    video_id: str,
    channel_id: str,
    thread_id: str,
    parent_comment_id: str | None,
    reply_count: int,
) -> dict[str, Any]:
    comment_id = _required_string(comment, "id")
    snippet = _required_dict(comment, "snippet")
    text_original = snippet.get("textOriginal") or snippet.get("textDisplay")
    if not isinstance(text_original, str) or not text_original:
        raise ValueError(f"comment {comment_id} has no text")

    return {
        "mention_id": f"youtube_data_api:{comment_id}",
        "provider": "youtube_data_api",
        "comment_id": comment_id,
        "comment_thread_id": thread_id,
        "parent_comment_id": parent_comment_id,
        "is_top_level": parent_comment_id is None,
        "video_id": video_id,
        "channel_id": channel_id,
        "source_url": f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
        "text_original": text_original,
        "published_at": _required_string(snippet, "publishedAt"),
        "updated_at": snippet.get("updatedAt"),
        "collected_at": collection["collected_at"],
        "refreshed_at": collection["refreshed_at"],
        "refresh_or_delete_at": collection["refresh_or_delete_at"],
        "like_count": int(snippet.get("likeCount", 0)),
        "reply_count": reply_count,
        "detected_language": "unknown",
        "region": "unknown",
        "author_reference": None,
        "raw_object_ref": f"{collection['raw_object_ref']}#{comment_id}",
        "etag": comment.get("etag"),
        "deletion_status": "active",
    }


def _required_dict(container: dict[str, Any], key: str) -> dict[str, Any]:
    value = container.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _required_string(container: dict[str, Any], key: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _check_result(passed: bool, detail: dict[str, Any]) -> dict[str, Any]:
    return {"status": "PASS" if passed else "FAIL", "detail": detail}
