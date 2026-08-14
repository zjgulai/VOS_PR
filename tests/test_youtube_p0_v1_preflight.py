from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "youtube_p0" / "v1_preflight_pending.json"
REQUIRED_RIGHTS = {"R1", "R4", "R5", "R6", "R17", "R18", "R19"}


class YouTubeP0V1PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def contract(self):
        module_name = "tools.social.youtube_p0_v1"
        spec = importlib.util.find_spec(module_name)
        self.assertIsNotNone(spec, "youtube_p0_v1 module must exist")
        return importlib.import_module(module_name)

    def approved_record(self) -> dict:
        record = deepcopy(self.fixture)
        record["rights"] = {right: "APPROVED_WITH_CONDITIONS" for right in REQUIRED_RIGHTS}
        record["rights_evidence"] = {
            right: f"fixture-approval:{right}" for right in REQUIRED_RIGHTS
        }
        record["rights_conditions"] = {right: True for right in REQUIRED_RIGHTS}
        record["source_scope"]["status"] = "APPROVED"
        record["source_scope"]["evidence_ref"] = "fixture-approval:source-scope"
        record["live_readonly_approval"]["status"] = "APPROVED"
        record["live_readonly_approval"]["evidence_ref"] = "fixture-approval:live-readonly"
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

    def test_pending_record_is_no_go_with_each_blocker_visible(self) -> None:
        contract = self.contract()

        report = contract.evaluate_v1_preflight(self.fixture, environ={})

        self.assertEqual("NO_GO", report["overall_status"])
        self.assertFalse(report["live_request_allowed"])
        self.assertEqual(REQUIRED_RIGHTS, set(report["checks"]["rights"]["pending_rights"]))
        self.assertEqual("FAIL", report["checks"]["source_scope"]["status"])
        self.assertEqual("FAIL", report["checks"]["live_readonly_approval"]["status"])
        self.assertEqual("FAIL", report["checks"]["runtime_environment"]["status"])
        self.assertEqual("FAIL", report["checks"]["sample_ids"]["status"])
        self.assertEqual("FAIL", report["checks"]["runtime_secret"]["status"])

    def test_approved_record_with_runtime_key_is_ready_without_exposing_key(self) -> None:
        contract = self.contract()
        secret = "fixture-secret-must-not-appear"

        report = contract.evaluate_v1_preflight(
            self.approved_record(),
            environ={"YOUTUBE_API_KEY": secret},
        )

        self.assertEqual("READY", report["overall_status"])
        self.assertTrue(report["live_request_allowed"])
        self.assertTrue(report["checks"]["runtime_secret"]["present"])
        self.assertNotIn(secret, json.dumps(report, ensure_ascii=False))

    def test_one_pending_required_right_keeps_live_request_blocked(self) -> None:
        contract = self.contract()
        record = self.approved_record()
        record["rights"]["R19"] = "PENDING_REVIEW"

        report = contract.evaluate_v1_preflight(
            record,
            environ={"YOUTUBE_API_KEY": "fixture-secret"},
        )

        self.assertEqual("NO_GO", report["overall_status"])
        self.assertFalse(report["live_request_allowed"])
        self.assertEqual(["R19"], report["checks"]["rights"]["pending_rights"])

    def test_approved_status_without_evidence_keeps_live_request_blocked(self) -> None:
        contract = self.contract()
        record = self.approved_record()
        record["rights_evidence"]["R19"] = ""

        report = contract.evaluate_v1_preflight(
            record,
            environ={"YOUTUBE_API_KEY": "fixture-secret"},
        )

        self.assertEqual("NO_GO", report["overall_status"])
        self.assertFalse(report["live_request_allowed"])
        self.assertEqual(["R19"], report["checks"]["rights"]["missing_evidence_rights"])

    def test_conditional_approval_with_unmet_condition_keeps_live_request_blocked(self) -> None:
        contract = self.contract()
        record = self.approved_record()
        record["rights_conditions"]["R19"] = False

        report = contract.evaluate_v1_preflight(
            record,
            environ={"YOUTUBE_API_KEY": "fixture-secret"},
        )

        self.assertEqual("NO_GO", report["overall_status"])
        self.assertFalse(report["live_request_allowed"])
        self.assertEqual(
            ["R19"],
            report["checks"]["rights"]["unsatisfied_condition_rights"],
        )


if __name__ == "__main__":
    unittest.main()
