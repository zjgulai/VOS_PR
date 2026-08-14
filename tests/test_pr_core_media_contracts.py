from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.pr_intel.core_media.contracts import (
    CoverageStatus,
    PermissionStatus,
    RightsLabel,
    stable_id,
)
from tools.pr_intel.core_media.scope_loader import (
    load_scope,
    validate_scope_dict,
)


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "config" / "pr_core_media_p0_scope.json"


def valid_scope_dict() -> dict:
    return {
        "version": "1.0",
        "scope_id": "scope_pr_core_media_p0_us_en_pumping_v1",
        "scope_version": "1.0-draft",
        "status": "pending_business_signoff",
        "markets": ["US"],
        "languages": ["en"],
        "category": "pumping",
        "incremental_days": 30,
        "baseline_days": 180,
        "expected_outlets": 11,
        "expected_candidate_journalists": 48,
        "outlets": [
            {
                "canonical_name": name,
                "edition_status": "pending",
            }
            for name in (
                "Forbes Personal Shopper",
                "Consumer Reports",
                "Parents",
                "Babylist",
                "Made for Mums",
                "The Bump",
                "What to Expect",
                "BabyCenter",
                "Women’s Health",
                "MomJunction",
                "Good Housekeeping",
            )
        ],
        "source_workbook": {
            "path": "PMO/业务协作_社媒团队/momcozy pr 媒体关系全年规划表.xlsx",
            "sheet": "吸奶器核心媒体池",
            "approval_status": "requires_standard_xlsx",
        },
        "dictionary": {
            "path": "config/competitor_dictionary.json",
            "version": "1.0",
            "approval_status": "pending_business_signoff",
        },
        "gate0_ref": (
            "PRD/work_log/2026-08-14_PR核心媒体洞察P0_"
            "业务与数据签字表-v1.0.md"
        ),
    }


class StableIdTests(unittest.TestCase):
    def test_normalization_keeps_id_repeatable_and_namespaced(self) -> None:
        first = stable_id("outlet", "Babylist")
        second = stable_id("outlet", "  BABYLIST  ")

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("outlet_"))
        self.assertEqual(23, len(first))

    def test_id_changes_when_a_semantic_part_changes(self) -> None:
        us = stable_id("edition", "Babylist", "US", "en")
        gb = stable_id("edition", "Babylist", "GB", "en")

        self.assertNotEqual(us, gb)

    def test_invalid_prefix_or_length_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "prefix"):
            stable_id("Outlet Name", "Babylist")
        with self.assertRaisesRegex(ValueError, "length"):
            stable_id("outlet", "Babylist", length=7)


class ScopeContractTests(unittest.TestCase):
    def test_scope_rejects_non_us_market_and_more_than_180_days(self) -> None:
        scope = valid_scope_dict()
        scope["markets"] = ["US", "GB"]
        scope["baseline_days"] = 181

        codes = {item.code for item in validate_scope_dict(scope)}

        self.assertEqual(
            {"p0_market_out_of_scope", "baseline_window_exceeded"},
            codes,
        )

    def test_scope_rejects_wrong_counts_and_duplicate_outlets(self) -> None:
        scope = valid_scope_dict()
        scope["expected_outlets"] = 10
        scope["expected_candidate_journalists"] = 47
        scope["outlets"][-1]["canonical_name"] = "Babylist"

        codes = {item.code for item in validate_scope_dict(scope)}

        self.assertEqual(
            {
                "expected_outlet_count_must_be_11",
                "expected_journalist_count_must_be_48",
                "outlet_count_mismatch",
                "duplicate_outlet",
            },
            codes,
        )

    def test_scope_rejects_out_of_scope_language_category_and_incremental_window(self) -> None:
        scope = valid_scope_dict()
        scope["languages"] = ["en", "fr"]
        scope["category"] = "feeding"
        scope["incremental_days"] = 31

        codes = {item.code for item in validate_scope_dict(scope)}

        self.assertEqual(
            {
                "p0_language_out_of_scope",
                "p0_category_out_of_scope",
                "incremental_window_must_be_30",
            },
            codes,
        )

    def test_project_scope_file_loads_with_exact_p0_boundaries(self) -> None:
        scope = load_scope(SCOPE_PATH)

        self.assertEqual(("US",), scope.markets)
        self.assertEqual(("en",), scope.languages)
        self.assertEqual("pumping", scope.category)
        self.assertEqual(30, scope.incremental_days)
        self.assertEqual(180, scope.baseline_days)
        self.assertEqual(11, len(scope.outlets))
        self.assertEqual(48, scope.expected_candidate_journalists)
        self.assertTrue(all(item.edition_status == "pending" for item in scope.outlets))

    def test_load_scope_reports_all_contract_violations(self) -> None:
        invalid = valid_scope_dict()
        invalid["markets"] = []
        invalid["baseline_days"] = 365

        with TemporaryDirectory() as directory:
            path = Path(directory) / "scope.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError,
                "p0_market_out_of_scope.*baseline_window_exceeded",
            ):
                load_scope(path)


class EnumContractTests(unittest.TestCase):
    def test_critical_status_values_remain_distinct(self) -> None:
        self.assertEqual("no_match", CoverageStatus.NO_MATCH.value)
        self.assertEqual(
            "source_unavailable",
            CoverageStatus.SOURCE_UNAVAILABLE.value,
        )
        self.assertNotEqual(
            CoverageStatus.NO_MATCH.value,
            CoverageStatus.UNKNOWN.value,
        )
        self.assertEqual("manual_only", PermissionStatus.MANUAL_ONLY.value)
        self.assertEqual("metadata_only", RightsLabel.METADATA_ONLY.value)


if __name__ == "__main__":
    unittest.main()
