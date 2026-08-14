from __future__ import annotations

import json
import tempfile
import threading
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tools.pr_intel.core_media.connectors.base import (
    CollectionBlocked,
    CollectionRequest,
    assert_collection_allowed,
    load_capabilities,
    validate_capabilities,
)
from tools.pr_intel.core_media.connectors.author_page import AuthorPageConnector
from tools.pr_intel.core_media.connectors.manual_url import (
    ManualSubmission,
    ManualUrlConnector,
)
from tools.pr_intel.core_media.connectors.rss import RssConnector
from tools.pr_intel.core_media.contracts import (
    CoverageStatus,
    PermissionStatus,
    RightsLabel,
)
from tools.pr_intel.core_media.scope_loader import load_scope


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "config/pr_core_media_p0_scope.json"
CAPABILITIES_PATH = ROOT / "config/pr_core_media_source_capabilities.json"
SYNTHETIC_PATH = ROOT / "tests/fixtures/pr_core_media/source_capabilities_synthetic.json"
HTTP_FIXTURES = ROOT / "tests/fixtures/pr_core_media/http"


class SourceCapabilityTests(unittest.TestCase):
    def test_project_registry_has_eight_pending_auto_and_eleven_manual_sources(self) -> None:
        capabilities = load_capabilities(CAPABILITIES_PATH)

        self.assertEqual(19, len(capabilities))
        self.assertEqual(19, len({item.source_id for item in capabilities}))
        self.assertEqual(
            8,
            sum(item.collection_method == "rss" for item in capabilities),
        )
        self.assertEqual(
            11,
            sum(item.collection_method == "manual_url" for item in capabilities),
        )

    def test_every_p0_outlet_has_capability_and_manual_fallback(self) -> None:
        scope = load_scope(SCOPE_PATH)
        capabilities = load_capabilities(CAPABILITIES_PATH)

        audit = validate_capabilities(scope, capabilities, offline=True)

        self.assertEqual(11, audit.covered_scope_outlets)
        self.assertEqual((), audit.outlets_without_capability)
        self.assertEqual((), audit.outlets_without_manual_fallback)
        self.assertEqual(8, len(audit.pending_permission_sources))
        self.assertEqual(19, len(audit.missing_retention_sources))
        self.assertEqual((), audit.rights_field_conflicts)
        self.assertFalse(audit.live_readonly_smoke_allowed)
        self.assertEqual(0, audit.network_requests_made)

    def test_pending_automatic_source_cannot_make_request(self) -> None:
        capability = next(
            item
            for item in load_capabilities(SYNTHETIC_PATH)
            if item.collection_method == "rss"
        )
        request = CollectionRequest(
            source_id=capability.source_id,
            edition_id=capability.edition_id,
            requested_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
            requested_end=datetime(2026, 8, 14, tzinfo=timezone.utc),
            purpose="incremental_monitoring",
            offline=False,
            manual_submission=False,
        )

        with self.assertRaisesRegex(CollectionBlocked, "permission_pending"):
            assert_collection_allowed(capability, request)

    def test_manual_only_source_accepts_manual_submission_but_not_network_collection(self) -> None:
        capability = next(
            item
            for item in load_capabilities(SYNTHETIC_PATH)
            if item.collection_method == "manual_url"
        )
        base = CollectionRequest(
            source_id=capability.source_id,
            edition_id=capability.edition_id,
            requested_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
            requested_end=datetime(2026, 8, 14, tzinfo=timezone.utc),
            purpose="manual_submission",
            offline=True,
            manual_submission=True,
        )

        assert_collection_allowed(capability, base)
        with self.assertRaisesRegex(CollectionBlocked, "manual_submission_required"):
            assert_collection_allowed(
                capability,
                replace(base, offline=False, manual_submission=False),
            )

    def test_bad_fallback_reference_is_reported_without_network(self) -> None:
        scope = load_scope(SCOPE_PATH)
        capabilities = list(load_capabilities(CAPABILITIES_PATH))
        automatic_index = next(
            index
            for index, item in enumerate(capabilities)
            if item.collection_method == "rss"
        )
        capabilities[automatic_index] = replace(
            capabilities[automatic_index], fallback_source_id="missing_manual_source"
        )

        audit = validate_capabilities(scope, capabilities, offline=True)

        self.assertIn(
            capabilities[automatic_index].source_id,
            audit.fallback_reference_errors,
        )
        self.assertEqual(0, audit.network_requests_made)

    def test_loader_rejects_literal_credentials(self) -> None:
        payload = json.loads(SYNTHETIC_PATH.read_text(encoding="utf-8"))
        payload["capabilities"][0]["credential_ref"] = "plain-text-token"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "credential_ref_must_be_secret_ref"):
                load_capabilities(path)


class _FixtureHandler(BaseHTTPRequestHandler):
    request_count = 0

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        type(self).request_count += 1
        routes = {
            "/feed.xml": (200, "application/rss+xml", "rss_with_gaps.xml", {}),
            "/empty.xml": (200, "application/rss+xml", "rss_empty.xml", {}),
            "/broken": (200, "text/html", "author_page_schema_changed.html", {}),
            "/author.html": (200, "text/html", "author_page.html", {}),
            "/author-changed.html": (
                200,
                "text/html",
                "author_page_schema_changed.html",
                {},
            ),
            "/forbidden": (403, "text/plain", None, {}),
            "/rate": (429, "text/plain", None, {"Retry-After": "17"}),
            "/missing": (404, "text/plain", None, {}),
        }
        status, content_type, fixture_name, headers = routes.get(
            self.path, (500, "text/plain", None, {})
        )
        body = (
            (HTTP_FIXTURES / fixture_name).read_bytes()
            if fixture_name is not None
            else b"fixture response"
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class CoreMediaConnectorHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _FixtureHandler.request_count = 0
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self) -> None:
        capabilities = load_capabilities(SYNTHETIC_PATH)
        self.pending_rss = next(
            item for item in capabilities if item.collection_method == "rss"
        )
        self.manual = next(
            item for item in capabilities if item.collection_method == "manual_url"
        )

    def _request(self, capability, *, manual: bool = False) -> CollectionRequest:
        return CollectionRequest(
            source_id=capability.source_id,
            edition_id=capability.edition_id,
            requested_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
            requested_end=datetime(2026, 8, 14, tzinfo=timezone.utc),
            purpose="fixture_test",
            offline=manual,
            manual_submission=manual,
        )

    def _approved_rss(self, path: str):
        return replace(
            self.pending_rss,
            entrypoint=f"{self.base_url}{path}",
            permission_status=PermissionStatus.APPROVED,
            rights_label=RightsLabel.EXCERPT_ONLY,
            retention_days=30,
            access_status="ready",
        )

    def test_policy_block_happens_before_any_http_request(self) -> None:
        before = _FixtureHandler.request_count
        blocked = replace(
            self.pending_rss,
            entrypoint=f"{self.base_url}/feed.xml",
        )

        with self.assertRaisesRegex(CollectionBlocked, "permission_pending"):
            RssConnector(blocked).collect(self._request(blocked))

        self.assertEqual(before, _FixtureHandler.request_count)

    def test_rss_deduplicates_urls_and_marks_missing_date_partial(self) -> None:
        capability = self._approved_rss("/feed.xml")

        result = RssConnector(capability).collect(self._request(capability))

        self.assertEqual(CoverageStatus.PARTIAL, result.coverage_status)
        self.assertEqual(3, result.items_seen)
        self.assertEqual(2, result.items_accepted)
        self.assertEqual(2, len(result.records))
        self.assertIsNone(result.records[1].published_at)
        self.assertEqual("duplicate_url", result.review_items[0].code)

    def test_rss_zero_403_429_and_bad_xml_remain_distinct(self) -> None:
        cases = (
            ("/empty.xml", CoverageStatus.NO_MATCH, None, None),
            ("/forbidden", CoverageStatus.SOURCE_UNAVAILABLE, "http_403_forbidden", None),
            ("/rate", CoverageStatus.RATE_LIMITED, "http_429_rate_limited", 17),
            ("/broken", CoverageStatus.SCHEMA_CHANGED, "rss_parse_failed", None),
        )
        for path, status, error_code, retry_after in cases:
            with self.subTest(path=path):
                capability = self._approved_rss(path)
                result = RssConnector(capability).collect(self._request(capability))
                self.assertEqual(status, result.coverage_status)
                self.assertEqual(error_code, result.error_code)
                self.assertEqual(retry_after, result.retry_after_seconds)

    def test_author_page_handles_valid_schema_change_and_404(self) -> None:
        selectors = (
            ("item", "article.story"),
            ("title", "h2 a"),
            ("link", "h2 a"),
            ("published_at", "time"),
            ("author", ".byline"),
        )
        for path, status in (
            ("/author.html", CoverageStatus.PARTIAL),
            ("/author-changed.html", CoverageStatus.SCHEMA_CHANGED),
            ("/missing", CoverageStatus.PROFILE_INVALID),
        ):
            with self.subTest(path=path):
                capability = replace(
                    self.pending_rss,
                    source_id=f"author_fixture_{path.strip('/').replace('.', '_')}",
                    collection_method="author_page",
                    source_type="author_page_fixture",
                    entrypoint=f"{self.base_url}{path}",
                    permission_status=PermissionStatus.APPROVED,
                    rights_label=RightsLabel.METADATA_ONLY,
                    retention_days=30,
                    access_status="ready",
                    selectors=selectors,
                )
                result = AuthorPageConnector(capability).collect(
                    self._request(capability)
                )
                self.assertEqual(status, result.coverage_status)
                if path == "/author.html":
                    self.assertEqual(2, result.items_accepted)
                    self.assertIsNone(result.records[1].published_at)

    def test_manual_url_filters_fields_and_queues_edition_mismatch(self) -> None:
        submitted_at = datetime(2026, 8, 14, tzinfo=timezone.utc)
        submissions = (
            ManualSubmission(
                submitted_url="https://example.test/manual/valid",
                edition_id=self.manual.edition_id,
                submitted_by_role="pr_analyst",
                submitted_at=submitted_at,
                rights_label=RightsLabel.METADATA_ONLY,
                title="Manual valid record",
                author_text="Editor One",
                published_at="2026-08-12T10:00:00Z",
                summary_excerpt="must be removed for metadata-only rights",
                extra_fields={"private_note": "must never be retained"},
            ),
            ManualSubmission(
                submitted_url="https://example.test/manual/wrong-edition",
                edition_id="edition_wrong",
                submitted_by_role="pr_analyst",
                submitted_at=submitted_at,
                rights_label=RightsLabel.METADATA_ONLY,
                title="Wrong edition",
            ),
        )

        result = ManualUrlConnector(self.manual).collect(
            self._request(self.manual, manual=True), submissions
        )

        self.assertEqual(CoverageStatus.PARTIAL, result.coverage_status)
        self.assertEqual(2, result.items_seen)
        self.assertEqual(1, result.items_accepted)
        self.assertIsNone(result.records[0].summary_excerpt)
        self.assertEqual("edition_mismatch", result.review_items[0].code)


if __name__ == "__main__":
    unittest.main()
