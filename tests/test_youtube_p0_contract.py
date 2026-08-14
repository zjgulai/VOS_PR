from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "youtube_p0" / "v0_fixture.json"


class YouTubeP0ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def contract(self):
        module_name = "tools.social.youtube_p0_contract"
        spec = importlib.util.find_spec(module_name)
        self.assertIsNotNone(spec, "youtube_p0_contract module must exist")
        return importlib.import_module(module_name)

    def test_source_scope_fixture_satisfies_v0_contract(self) -> None:
        contract = self.contract()

        errors = contract.validate_source_scope(self.fixture["scope"])

        self.assertEqual([], errors)

    def test_normalization_deduplicates_embedded_replies_and_keeps_parent_links(self) -> None:
        contract = self.contract()

        records = contract.normalize_fixture_comments(self.fixture)

        self.assertEqual(3, len(records))
        self.assertEqual(
            {
                "comment_top_fixture_001",
                "comment_reply_fixture_001",
                "comment_reply_fixture_002",
            },
            {record["comment_id"] for record in records},
        )
        top = next(record for record in records if record["comment_id"] == "comment_top_fixture_001")
        replies = [record for record in records if not record["is_top_level"]]
        self.assertIsNone(top["parent_comment_id"])
        self.assertEqual(2, top["reply_count"])
        self.assertEqual(
            {"comment_top_fixture_001"},
            {record["parent_comment_id"] for record in replies},
        )
        self.assertTrue(all(record["region"] == "unknown" for record in records))
        self.assertTrue(all(record["detected_language"] == "unknown" for record in records))

    def test_normalization_is_idempotent_for_the_same_fixture(self) -> None:
        contract = self.contract()

        first = contract.normalize_fixture_comments(self.fixture)
        second = contract.normalize_fixture_comments(self.fixture)

        self.assertEqual(first, second)
        self.assertEqual(len(first), len({record["mention_id"] for record in first}))

    def test_coverage_cases_map_to_distinct_statuses(self) -> None:
        contract = self.contract()

        actual = {
            case["name"]: contract.map_coverage_status(**case["input"])
            for case in self.fixture["coverage_cases"]
        }
        expected = {case["name"]: case["expected"] for case in self.fixture["coverage_cases"]}

        self.assertEqual(expected, actual)

    def test_lifecycle_targets_locate_raw_and_derived_objects(self) -> None:
        contract = self.contract()

        targets = contract.locate_lifecycle_targets(
            self.fixture["lifecycle_records"],
            "comment_top_fixture_001",
        )

        self.assertEqual("mention_fixture_top_001", targets["record_id"])
        self.assertEqual(["evidence_fixture_001"], targets["evidence_ids"])
        self.assertEqual(["insight_fixture_001"], targets["insight_ids"])
        self.assertEqual(["action_fixture_001"], targets["action_ids"])

    def test_lifecycle_actions_distinguish_refresh_source_missing_and_delete_request(self) -> None:
        contract = self.contract()
        records = {record["comment_id"]: record for record in self.fixture["lifecycle_records"]}

        refresh = contract.lifecycle_action(records["comment_top_fixture_001"], "2026-09-13T00:00:00Z")
        missing = contract.lifecycle_action(records["comment_missing_fixture_001"], "2026-08-14T00:00:00Z")
        delete = contract.lifecycle_action(records["comment_delete_fixture_001"], "2026-08-14T00:00:00Z")

        self.assertEqual("refresh_due", refresh)
        self.assertEqual("mark_source_missing", missing)
        self.assertEqual("delete_due_to_request", delete)

    def test_static_audit_flags_profile_read_silent_exception_and_hardcoded_scope(self) -> None:
        contract = self.contract()
        self.assertTrue(hasattr(contract, "audit_python_source_text"))
        unsafe_source = '''
from dataclasses import dataclass

try:
    content = open("~/.zshrc").read()
except Exception:
    pass

@dataclass
class UnsafeVideo:
    APIFY_API_KEY: str = "fixture-hardcoded-secret"
    country_code: str = "US"
    language: str = "en"
'''

        findings = contract.audit_python_source_text(unsafe_source)

        self.assertEqual(
            {
                "hardcoded_secret",
                "personal_profile_read",
                "silent_broad_exception",
                "unverified_scope_default",
            },
            {finding["code"] for finding in findings},
        )

    def test_v0_report_passes_all_six_offline_gates(self) -> None:
        contract = self.contract()
        self.assertTrue(hasattr(contract, "build_v0_report"))
        collector_path = ROOT / "tools" / "social" / "youtube_collector.py"

        report = contract.build_v0_report(self.fixture, collector_path)

        self.assertEqual("PASS", report["overall_status"])
        self.assertEqual(
            {
                "source_scope_schema",
                "comment_thread_reply_normalization",
                "coverage_status_mapping",
                "secret_and_profile_safety",
                "silent_exception_safety",
                "lifecycle_locatability",
            },
            set(report["checks"]),
        )
        self.assertTrue(all(check["status"] == "PASS" for check in report["checks"].values()))
        self.assertEqual(3, report["metrics"]["normalized_comments"])
        self.assertEqual(10, report["metrics"]["coverage_cases"])

    def test_v0_report_rejects_empty_normalization_and_coverage_proof(self) -> None:
        contract = self.contract()
        fixture = deepcopy(self.fixture)
        fixture["comment_thread_pages"] = []
        fixture["reply_pages_by_parent"] = {}
        fixture["coverage_cases"] = []

        report = contract.build_v0_report(
            fixture,
            ROOT / "tools" / "social" / "youtube_collector.py",
        )

        self.assertEqual(
            "FAIL",
            report["checks"]["comment_thread_reply_normalization"]["status"],
        )
        self.assertEqual("FAIL", report["checks"]["coverage_status_mapping"]["status"])

    def test_v0_report_requires_fixture_only_marker(self) -> None:
        contract = self.contract()
        fixture = deepcopy(self.fixture)
        fixture["fixture_only"] = False

        report = contract.build_v0_report(
            fixture,
            ROOT / "tools" / "social" / "youtube_collector.py",
        )

        self.assertEqual("NO_GO", report["overall_status"])
        self.assertEqual("FAIL", report["checks"]["source_scope_schema"]["status"])


if __name__ == "__main__":
    unittest.main()
