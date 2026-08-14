from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from tools.etl.apply_pr_core_media_migrations import apply_migrations
from tools.pr_intel.core_media.storage import PrMediaRepository
from tools.pr_intel.core_media.workbook_importer import (
    ImportApprovalError,
    approve_workbook_import,
    preview_workbook,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pr_core_media/core_media_pool_synthetic.xlsx"
SHEET = "吸奶器核心媒体池"


class WorkbookPreviewTests(unittest.TestCase):
    def test_merged_outlet_fields_only_inherit_within_group(self) -> None:
        batch = preview_workbook(FIXTURE, SHEET, "fixture-v1")

        self.assertEqual(2, len(batch.outlets))
        self.assertEqual(3, len(batch.journalists))
        self.assertEqual("Outlet Alpha", batch.outlets[0].canonical_name)
        self.assertEqual("Outlet Beta", batch.outlets[1].canonical_name)
        self.assertEqual(2, len({item.outlet_id for item in batch.affiliations}))
        self.assertTrue(all(item.source_row_ref for item in batch.journalists))

    def test_editor_fields_do_not_forward_fill_and_urls_are_typed(self) -> None:
        batch = preview_workbook(FIXTURE, SHEET, "fixture-v1")

        journalists = {item.public_name: item for item in batch.journalists}
        self.assertIsNone(journalists["Editor Two"].public_title)
        self.assertEqual("Features Editor", journalists["Editor Three"].public_title)
        self.assertEqual(
            {"author_page", "linkedin", "instagram", "x"},
            {item.platform for item in batch.touchpoints},
        )
        linkedin = next(item for item in batch.touchpoints if item.platform == "linkedin")
        self.assertEqual("manual_verification_only", linkedin.collection_policy)

    def test_preview_reports_blank_editor_and_edition_conflict_without_guessing(self) -> None:
        batch = preview_workbook(FIXTURE, SHEET, "fixture-v1")

        self.assertEqual(1, batch.blank_editor_rows)
        self.assertEqual(1, len(batch.review_items_by_code("edition_conflict")))
        conflicted = next(
            item for item in batch.editions if item.outlet_id == batch.outlets[1].outlet_id
        )
        self.assertEqual("US", conflicted.country)
        self.assertEqual("pending", conflicted.status)
        self.assertIsNone(conflicted.canonical_domain)

    def test_preview_is_deterministic_and_serializable(self) -> None:
        first = preview_workbook(FIXTURE, SHEET, "fixture-v1")
        second = preview_workbook(FIXTURE, SHEET, "fixture-v1")

        self.assertEqual(first.source_file_sha256, second.source_file_sha256)
        self.assertEqual(first.outlets, second.outlets)
        payload = first.to_preview_dict()
        json.dumps(payload, ensure_ascii=False)
        self.assertEqual(2, payload["counts"]["outlets"])
        self.assertEqual(3, payload["counts"]["journalists"])


class WorkbookApproveTests(unittest.TestCase):
    def test_approve_requires_admin_role(self) -> None:
        batch = preview_workbook(FIXTURE, SHEET, "fixture-v1")
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "registry.duckdb"
            apply_migrations(db_path)
            repository = PrMediaRepository(db_path)

            with self.assertRaisesRegex(ImportApprovalError, "admin_role_required"):
                approve_workbook_import(repository, batch, "viewer")

    def test_approved_import_writes_new_version_atomically(self) -> None:
        batch = preview_workbook(FIXTURE, SHEET, "fixture-v1")
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "registry.duckdb"
            apply_migrations(db_path)
            repository = PrMediaRepository(db_path)

            report = approve_workbook_import(repository, batch, "admin")

            self.assertEqual("approved", report.status)
            self.assertEqual(2, report.outlet_count)
            self.assertEqual(3, report.journalist_count)
            con = duckdb.connect(str(db_path), read_only=True)
            try:
                self.assertEqual(
                    1,
                    con.execute(
                        "SELECT count(*) FROM pr_core_media.ctl_import_batch"
                    ).fetchone()[0],
                )
                self.assertEqual(
                    2,
                    con.execute("SELECT count(*) FROM pr_core_media.dim_outlet").fetchone()[0],
                )
                self.assertEqual(
                    3,
                    con.execute(
                        "SELECT count(*) FROM pr_core_media.dim_journalist"
                    ).fetchone()[0],
                )
            finally:
                con.close()

            duplicate = approve_workbook_import(repository, batch, "admin")
            self.assertEqual("failed", duplicate.status)
            self.assertEqual(1, len(duplicate.errors))


if __name__ == "__main__":
    unittest.main()
