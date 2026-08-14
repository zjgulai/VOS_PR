from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from tools.etl.apply_pr_core_media_migrations import apply_migrations
from tests.test_pr_core_media_migrations import MIGRATION_DIR, seed_lifecycle_graph


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "app/dashboard/backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from main import app  # noqa: E402


class PrMediaApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.db = Path(self.directory.name) / "api.duckdb"
        apply_migrations(self.db, MIGRATION_DIR)
        seed_lifecycle_graph(self.db)
        app.state.pr_media_db_path = self.db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        if hasattr(app.state, "pr_media_db_path"):
            delattr(app.state, "pr_media_db_path")
        self.directory.cleanup()

    def test_overview_registry_and_pagination_contract(self) -> None:
        overview = self.client.get("/api/v1/pr-media/overview")
        self.assertEqual(200, overview.status_code)
        self.assertEqual(1, overview.json()["registry"]["outlets"])
        self.assertEqual(1, overview.json()["registry"]["candidate_journalists"])

        outlets = self.client.get(
            "/api/v1/pr-media/registry/outlets", params={"page": 1, "page_size": 1}
        )
        self.assertEqual(200, outlets.status_code)
        self.assertEqual(1, outlets.json()["total"])
        self.assertEqual("Fixture Outlet", outlets.json()["items"][0]["canonical_name"])

        invalid = self.client.get(
            "/api/v1/pr-media/registry/outlets", params={"page_size": 101}
        )
        self.assertEqual(422, invalid.status_code)
        self.assertEqual("request_validation_failed", invalid.json()["code"])
        self.assertTrue(invalid.json()["request_id"])

    def test_empty_coverage_is_unknown_not_a_false_zero(self) -> None:
        response = self.client.get("/api/v1/pr-media/coverage")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual([], payload["items"])
        self.assertEqual("unknown", payload["summary"]["status"])
        self.assertIsNone(payload["summary"]["documents_accepted"])

    def test_brief_list_detail_and_evidence_are_bounded(self) -> None:
        listed = self.client.get("/api/v1/pr-media/briefs")
        self.assertEqual(200, listed.status_code)
        self.assertEqual(1, listed.json()["total"])

        detail = self.client.get("/api/v1/pr-media/briefs/brief_fixture")
        self.assertEqual(200, detail.status_code)
        payload = detail.json()
        self.assertEqual("brief_fixture", payload["brief_id"])
        self.assertLessEqual(len(payload["evidence"]), 20)
        serialized = json.dumps(payload)
        self.assertNotIn("raw_object_ref", serialized)
        self.assertNotIn("full_body", serialized)

    def test_brief_review_enforces_role_and_optimistic_status(self) -> None:
        forbidden = self.client.post(
            "/api/v1/pr-media/briefs/brief_fixture/review",
            json={
                "command": "approve",
                "actor_role": "viewer",
                "expected_status": "draft",
                "note": "fixture",
            },
            headers={"X-Request-ID": "request_forbidden_fixture"},
        )
        self.assertEqual(403, forbidden.status_code)
        self.assertEqual("review_role_forbidden", forbidden.json()["code"])
        self.assertEqual("request_forbidden_fixture", forbidden.json()["request_id"])

        approved = self.client.post(
            "/api/v1/pr-media/briefs/brief_fixture/review",
            json={
                "command": "approve",
                "actor_role": "pr_analyst",
                "expected_status": "draft",
                "note": "Evidence reviewed",
            },
        )
        self.assertEqual(200, approved.status_code)
        self.assertEqual("approved", approved.json()["review_status"])

        conflict = self.client.post(
            "/api/v1/pr-media/briefs/brief_fixture/review",
            json={
                "command": "reject",
                "actor_role": "pr_analyst",
                "expected_status": "draft",
                "note": "stale request",
            },
        )
        self.assertEqual(409, conflict.status_code)
        self.assertEqual("brief_status_conflict", conflict.json()["code"])

    def test_action_requires_approval_before_execution_and_persists_audit(self) -> None:
        approve_brief = self.client.post(
            "/api/v1/pr-media/briefs/brief_fixture/review",
            json={
                "command": "approve",
                "actor_role": "pr_analyst",
                "expected_status": "draft",
                "note": "Evidence reviewed",
            },
        )
        self.assertEqual(200, approve_brief.status_code)
        created = self.client.post(
            "/api/v1/pr-media/actions",
            json={
                "brief_id": "brief_fixture",
                "created_by_role": "pr_analyst",
                "action_type": "media_pitch",
                "title": "Fixture API pitch",
                "why_now": "Recent covered competitor comparison",
                "target_outlet_text": "Fixture Outlet",
                "target_journalist_text": "Editor Fixture",
                "content_angle": "Independent comfort evidence",
                "required_assets": ["lab_data"],
                "owner_role": "media_relations_lead",
                "due_at": "2026-08-20T00:00:00Z",
                "success_metric": "Decision recorded",
                "risk_text": "No unsupported product claim",
                "source_insight_ids": ["signal_fixture"],
            },
        )
        self.assertEqual(201, created.status_code, created.text)
        action_id = created.json()["action_id"]
        self.assertEqual("pending", created.json()["approval_status"])

        premature = self.client.post(
            f"/api/v1/pr-media/actions/{action_id}/transition",
            json={"command": "start", "actor_role": "media_relations_lead"},
        )
        self.assertEqual(409, premature.status_code)
        self.assertEqual("approval_required", premature.json()["code"])

        forbidden = self.client.post(
            f"/api/v1/pr-media/actions/{action_id}/approve",
            json={"actor_role": "viewer", "expected_status": "pending"},
        )
        self.assertEqual(403, forbidden.status_code)

        approved = self.client.post(
            f"/api/v1/pr-media/actions/{action_id}/approve",
            json={
                "actor_role": "pr_lead",
                "expected_status": "pending",
                "note": "Approved fixture wording",
            },
        )
        self.assertEqual(200, approved.status_code)
        started = self.client.post(
            f"/api/v1/pr-media/actions/{action_id}/transition",
            json={"command": "start", "actor_role": "media_relations_lead"},
        )
        self.assertEqual(200, started.status_code)
        self.assertEqual("in_progress", started.json()["execution_status"])

        missing_result = self.client.post(
            f"/api/v1/pr-media/actions/{action_id}/transition",
            json={"command": "complete", "actor_role": "media_relations_lead"},
        )
        self.assertEqual(422, missing_result.status_code)
        completed = self.client.post(
            f"/api/v1/pr-media/actions/{action_id}/transition",
            json={
                "command": "complete",
                "actor_role": "media_relations_lead",
                "note": "Fixture result recorded",
            },
        )
        self.assertEqual(200, completed.status_code)
        self.assertEqual("done", completed.json()["execution_status"])
        self.assertEqual(3, len(completed.json()["transition_history"]))

    def test_unavailable_database_returns_structured_503(self) -> None:
        app.state.pr_media_db_path = Path(self.directory.name) / "missing.duckdb"
        response = self.client.get(
            "/api/v1/pr-media/overview",
            headers={"X-Request-ID": "request_missing_db"},
        )
        self.assertEqual(503, response.status_code)
        self.assertEqual("pr_media_store_unavailable", response.json()["code"])
        self.assertEqual("request_missing_db", response.json()["request_id"])


if __name__ == "__main__":
    unittest.main()
