from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import importlib.util
import json
from pathlib import Path
import socket
import threading
import unittest
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
PENDING_RECORD = ROOT / "tests" / "fixtures" / "youtube_p0" / "v1_preflight_pending.json"


def _approved_record() -> dict:
    record = json.loads(PENDING_RECORD.read_text(encoding="utf-8"))
    rights = {"R1", "R4", "R5", "R6", "R17", "R18", "R19"}
    record["rights"] = {right: "APPROVED_WITH_CONDITIONS" for right in rights}
    record["rights_evidence"] = {right: f"fixture-approval:{right}" for right in rights}
    record["rights_conditions"] = {right: True for right in rights}
    record["source_scope"]["status"] = "APPROVED"
    record["source_scope"]["evidence_ref"] = "fixture-approval:source-scope"
    record["live_readonly_approval"] = {
        "status": "APPROVED",
        "evidence_ref": "fixture-approval:live-readonly",
    }
    record["runtime_environment"] = {
        "status": "APPROVED",
        "name": "fixture-approved-runtime",
        "evidence_ref": "fixture-approval:runtime",
    }
    record["secret_source"]["status"] = "APPROVED"
    record["secret_source"]["evidence_ref"] = "fixture-approval:secret-source"
    record["samples"] = {
        "channel_id": "UC_fixture_channel",
        "video_id": "fixture_video_001",
        "reply_parent_id": "fixture_comment_001",
    }
    return record


class _YouTubeFixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        self.server.requests.append(
            {
                "path": parsed.path,
                "query": query,
                "api_key": self.headers.get("X-Goog-Api-Key"),
            }
        )

        if parsed.path == "/youtube/v3/channels":
            if query.get("id") == ["UC_missing_channel"]:
                self._json(200, {"kind": "youtube#channelListResponse", "items": []})
                return
            payload = {
                "kind": "youtube#channelListResponse",
                "items": [
                    {
                        "id": "UC_fixture_channel",
                        "contentDetails": {
                            "relatedPlaylists": {"uploads": "UU_fixture_uploads"}
                        },
                    }
                ],
            }
            self._json(200, payload)
            return
        if parsed.path == "/youtube/v3/videos":
            payload = {
                "kind": "youtube#videoListResponse",
                "items": [
                    {
                        "id": "fixture_video_001",
                        "snippet": {
                            "channelId": "UC_fixture_channel",
                            "title": "Fixture video",
                            "publishedAt": "2026-08-01T00:00:00Z",
                        },
                        "status": {"privacyStatus": "public"},
                        "statistics": {"commentCount": "2"},
                    }
                ],
            }
            self._json(200, payload)
            return
        if parsed.path == "/youtube/v3/commentThreads":
            if query.get("videoId") == ["comments_disabled"]:
                self._json(
                    403,
                    {
                        "error": {
                            "code": 403,
                            "message": "Comments are disabled",
                            "errors": [{"reason": "commentsDisabled"}],
                        }
                    },
                )
                return
            payload = {
                "kind": "youtube#commentThreadListResponse",
                "items": [
                    {
                        "id": "fixture_thread_001",
                        "snippet": {
                            "videoId": "fixture_video_001",
                            "totalReplyCount": 1,
                            "topLevelComment": {
                                "id": "fixture_comment_001",
                                "snippet": {
                                    "textOriginal": "Fixture top-level comment",
                                    "publishedAt": "2026-08-02T00:00:00Z",
                                },
                            },
                        },
                    }
                ],
            }
            self._json(200, payload)
            return
        if parsed.path == "/youtube/v3/comments":
            payload = {
                "kind": "youtube#commentListResponse",
                "items": [
                    {
                        "id": "fixture_reply_001",
                        "snippet": {
                            "parentId": "fixture_comment_001",
                            "textOriginal": "Fixture reply",
                            "publishedAt": "2026-08-03T00:00:00Z",
                        },
                    }
                ],
            }
            self._json(200, payload)
            return
        self._json(404, {"error": {"errors": [{"reason": "notFound"}]}})

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


class YouTubeOfficialConnectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _YouTubeFixtureHandler)
        cls.server.requests = []
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}/youtube/v3"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self) -> None:
        self.server.requests.clear()

    def connector(self):
        module_name = "tools.social.youtube_official_connector"
        spec = importlib.util.find_spec(module_name)
        self.assertIsNotNone(spec, "youtube_official_connector module must exist")
        return importlib.import_module(module_name)

    def test_four_readonly_endpoints_use_documented_parameters_and_header_key(self) -> None:
        connector = self.connector()
        secret = "fixture-header-secret"

        with connector.YouTubeOfficialClient(
            api_key=secret,
            base_url=self.base_url,
        ) as client:
            access = client.validate_access("UC_fixture_channel")
            video = client.fetch_video("fixture_video_001")
            threads = client.fetch_comment_threads("fixture_video_001")
            replies = client.fetch_replies("fixture_comment_001")

        self.assertEqual("UU_fixture_uploads", access["uploads_playlist_id"])
        self.assertEqual("fixture_video_001", video["item"]["id"])
        self.assertEqual(1, len(threads["items"]))
        self.assertEqual(1, len(replies["items"]))
        self.assertEqual(
            ["/youtube/v3/channels", "/youtube/v3/videos", "/youtube/v3/commentThreads", "/youtube/v3/comments"],
            [request["path"] for request in self.server.requests],
        )
        self.assertTrue(all(request["api_key"] == secret for request in self.server.requests))
        self.assertEqual(["id,contentDetails"], self.server.requests[0]["query"]["part"])
        self.assertEqual(["snippet,status,statistics"], self.server.requests[1]["query"]["part"])
        self.assertEqual(["id,snippet,replies"], self.server.requests[2]["query"]["part"])
        self.assertEqual(["time"], self.server.requests[2]["query"]["order"])
        self.assertEqual(["plainText"], self.server.requests[2]["query"]["textFormat"])
        self.assertEqual(["100"], self.server.requests[2]["query"]["maxResults"])
        self.assertEqual(["id,snippet"], self.server.requests[3]["query"]["part"])
        self.assertNotIn(
            secret,
            json.dumps([access, video, threads, replies], ensure_ascii=False),
        )

    def test_comments_disabled_error_is_structured_and_secret_free(self) -> None:
        connector = self.connector()
        secret = "fixture-error-secret"

        with connector.YouTubeOfficialClient(
            api_key=secret,
            base_url=self.base_url,
        ) as client:
            with self.assertRaises(connector.YouTubeDataApiError) as caught:
                client.fetch_comment_threads("comments_disabled")

        error = caught.exception
        self.assertEqual(403, error.status_code)
        self.assertEqual("commentsDisabled", error.reason)
        self.assertEqual("comments_disabled", error.coverage_status)
        self.assertNotIn(secret, json.dumps(error.to_dict(), ensure_ascii=False))

    def test_channel_not_found_does_not_invent_an_unsupported_coverage_status(self) -> None:
        connector = self.connector()

        with connector.YouTubeOfficialClient(
            api_key="fixture-secret",
            base_url=self.base_url,
        ) as client:
            with self.assertRaises(connector.YouTubeDataApiError) as caught:
                client.validate_access("UC_missing_channel")

        error = caught.exception
        self.assertEqual("channelNotFound", error.reason)
        self.assertIsNone(error.coverage_status)

    def test_transport_failure_is_structured_and_secret_free(self) -> None:
        connector = self.connector()
        secret = "fixture-transport-secret"
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        _, unused_port = probe.getsockname()
        probe.close()

        with connector.YouTubeOfficialClient(
            api_key=secret,
            base_url=f"http://127.0.0.1:{unused_port}/youtube/v3",
            timeout_seconds=0.2,
        ) as client:
            with self.assertRaises(connector.YouTubeDataApiError) as caught:
                client.validate_access("UC_fixture_channel")

        error = caught.exception
        self.assertEqual(0, error.status_code)
        self.assertEqual("transportError", error.reason)
        self.assertEqual("transient_error", error.coverage_status)
        self.assertNotIn(secret, json.dumps(error.to_dict(), ensure_ascii=False))

    def test_comment_page_size_above_official_limit_is_rejected_before_request(self) -> None:
        connector = self.connector()

        with connector.YouTubeOfficialClient(
            api_key="fixture-secret",
            base_url=self.base_url,
        ) as client:
            with self.assertRaisesRegex(ValueError, "max_results must be between 1 and 100"):
                client.fetch_comment_threads("fixture_video_001", max_results=101)

        self.assertEqual([], self.server.requests)

    def test_readonly_smoke_returns_sanitized_evidence_from_all_endpoints(self) -> None:
        connector = self.connector()
        self.assertTrue(hasattr(connector, "run_v1_readonly_smoke"))
        secret = "fixture-smoke-secret"

        with connector.YouTubeOfficialClient(
            api_key=secret,
            base_url=self.base_url,
        ) as client:
            report = connector.run_v1_readonly_smoke(
                _approved_record(),
                environ={"YOUTUBE_API_KEY": secret},
                client=client,
            )

        serialized = json.dumps(report, ensure_ascii=False)
        self.assertEqual("PASS", report["overall_status"])
        self.assertTrue(report["live_request_attempted"])
        self.assertEqual(1, report["evidence"]["comment_threads"]["items_count"])
        self.assertEqual(1, report["evidence"]["replies"]["items_count"])
        self.assertNotIn(secret, serialized)
        self.assertNotIn("Fixture top-level comment", serialized)
        self.assertNotIn("Fixture reply", serialized)


if __name__ == "__main__":
    unittest.main()
