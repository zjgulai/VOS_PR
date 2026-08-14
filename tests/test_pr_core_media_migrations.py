from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import duckdb

from tools.etl.apply_pr_core_media_migrations import (
    MigrationChecksumError,
    apply_migrations,
    verify_schema_path,
)
from tools.pr_intel.core_media.storage import PrMediaRepository
from tools.pr_intel.core_media.lifecycle import (
    DeletionApprovalError,
    execute_approved_deletion,
    locate_lifecycle_targets,
)


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "tools" / "etl" / "migrations" / "pr_core_media"

EXPECTED_TABLES = {
    "schema_migrations",
    "ctl_import_batch",
    "ctl_import_record",
    "ctl_source_capability",
    "ctl_collection_job",
    "dim_outlet",
    "dim_outlet_edition",
    "dim_journalist",
    "bridge_journalist_affiliation",
    "dim_touchpoint",
    "ods_raw_envelope",
    "dwd_document",
    "bridge_document_byline",
    "dwd_editorial_signal",
    "dwd_claim",
    "dwd_evidence",
    "bridge_evidence_set_item",
    "dwd_relationship_event",
    "dwd_pitch_constraint",
    "dws_source_coverage",
    "dws_edition_period",
    "dws_journalist_period",
    "ads_media_brief",
    "ads_opportunity",
    "ads_media_risk",
    "ads_action",
    "ads_feedback",
    "ctl_deletion_audit",
    "ctl_deletion_target",
}


def seed_lifecycle_graph(db: Path) -> None:
    con = duckdb.connect(str(db))
    try:
        con.execute(
            """
            INSERT INTO pr_core_media.dim_outlet VALUES
            ('outlet_fixture', 'Fixture Outlet', 'review_media', 'review', 'verified',
             'fixture.xlsx', 'Core', 'Core!2', 'fixture-v1',
             '2026-08-14T00:00:00Z', '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dim_outlet_edition VALUES
            ('edition_fixture', 'outlet_fixture', 'US', 'en', 'example.test', 'pr_admin',
             'verified', '2026-08-14T00:00:00Z', 'fixture:evidence', 'fixture.xlsx',
             'Core', 'Core!2', 'fixture-v1', '2026-08-14T00:00:00Z',
             '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dim_journalist VALUES
            ('journalist_fixture', 'Editor Fixture', 'Commerce Editor', 'verified',
             '2026-08-14T00:00:00Z', 'fixture:identity', 'fixture.xlsx', 'Core',
             'Core!2', 'fixture-v1', '2026-08-14T00:00:00Z',
             '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.bridge_journalist_affiliation VALUES
            ('affiliation_fixture', 'journalist_fixture', 'edition_fixture', 'Commerce Editor',
             'active', 'https://example.test/authors/editor', '2026-01-01T00:00:00Z',
             NULL, '2026-08-14T00:00:00Z', 'fixture.xlsx', 'Core', 'Core!2',
             'fixture-v1', '2026-08-14T00:00:00Z', '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dim_touchpoint VALUES
            ('touchpoint_fixture', 'journalist', 'journalist_fixture', 'author_page',
             'https://example.test/authors/editor', 'public_professional', 'approved',
             'ready', '2026-08-14T00:00:00Z', 'fixture.xlsx', 'Core', 'Core!2',
             'fixture-v1', '2026-08-14T00:00:00Z', '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.ods_raw_envelope VALUES
            ('envelope_fixture', 'run_fixture', 'source_fixture', '2026-08-14T00:00:00Z',
             'payload_fixture', '/tmp/envelope_fixture.json', 'excerpt_only',
             '["title"]', '2026-09-13T00:00:00Z', 1, 'active',
             '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dwd_document VALUES
            ('document_fixture', 'source_fixture', 'edition_fixture', 'journalist_fixture',
             'https://example.test/article', '2026-08-12T00:00:00Z',
             '2026-08-14T00:00:00Z', 'Sensitive Fixture Title', 'Editor Fixture',
             'verified', 'review', 'unknown', 'text_hash_fixture', 'excerpt_only', false,
             NULL, 'active', '/tmp/envelope_fixture.json', '2026-08-14T00:00:00Z',
             '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.bridge_document_byline VALUES
            ('byline_fixture', 'document_fixture', 1, 'Editor Fixture',
             'journalist_fixture', 'verified', 'fixture:byline', '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dwd_editorial_signal VALUES
            ('signal_fixture', 'document_fixture', 'edition_fixture', 'journalist_fixture',
             'competitor_evaluation', 'Fixture Brand', 'pump', 'mixed', 'Fixture claim',
             'Fixture evidence span', 'unknown', 0.8, 'verified', 'evidence_set_fixture',
             'rule-v1', NULL, NULL, NULL, '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dwd_claim VALUES
            ('claim_fixture', 'Fixture claim', 'Editor Fixture', 'Fixture Brand', 'evaluates',
             '2026-08', 'verified', 0.8, '["US"]', '["Fixture Brand"]', NULL,
             'rule-v1', NULL, 'verified', '2026-08-14T00:00:00Z', NULL);
            INSERT INTO pr_core_media.dwd_evidence VALUES
            ('evidence_fixture', 'claim_fixture', 'document_fixture', 'Fixture quote',
             'supports', 'B', '2026-08-12T00:00:00Z', NULL, 'none',
             '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.bridge_evidence_set_item VALUES
            ('evidence_set_fixture', 'evidence_fixture', 1, '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dwd_relationship_event VALUES
            ('relationship_fixture', 'journalist_fixture', 'edition_fixture', 'contact',
             '2026-08-10T00:00:00Z', 'no_reply', 'media_relations', 'manual', 'Core!2',
             NULL, 'verified', '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dwd_pitch_constraint VALUES
            ('constraint_fixture', 'journalist_fixture', 'edition_fixture', 'recent_contact',
             '2026-08-10T00:00:00Z', '2026-09-09T00:00:00Z', 'active',
             'relationship_fixture', 'pr_lead', '2026-08-14T00:00:00Z',
             '2026-08-14T00:00:00Z', '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.dws_journalist_period VALUES
            ('journalist_fixture', '2026-08-01T00:00:00Z', '2026-08-14T00:00:00Z',
             '{}', '{}', 1, 'complete', '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.ads_media_brief VALUES
            ('brief_fixture', 'journalist', 'journalist_fixture', '2026-08-01T00:00:00Z',
             '2026-08-14T00:00:00Z', NULL, NULL, '2026-08-12T00:00:00Z',
             '2026-08-12T00:00:00Z', 1, '{}', NULL, 'not_present', NULL, NULL, 'observe',
             NULL, 'complete', '[]', 'evidence_set_fixture', 'rule-v1', NULL, 'rule-v1',
             NULL, 'verified', '2026-08-14T00:00:00Z', NULL);
            INSERT INTO pr_core_media.ads_opportunity VALUES
            ('opportunity_fixture', 'edition_fixture', 'journalist_fixture', 0.8, 0.7, 0.6,
             0.9, NULL, 0.0, 0.0, 'high', 'Fixture angle', 'Fixture timing',
             'evidence_set_fixture', 'verified', '2026-08-14T00:00:00Z',
             '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.ads_media_risk VALUES
            ('risk_fixture', 'document_fixture', 'edition_fixture', 'journalist_fixture',
             'quality', 'direct', 'direct', 'direct', 'Fixture risk span', 'unknown',
             'review', 'verified', NULL, 'evidence_set_fixture',
             '2026-08-14T00:00:00Z', '2026-08-14T00:00:00Z');
            INSERT INTO pr_core_media.ads_action VALUES
            ('action_fixture', 'observe', 'Fixture Action', 'Fixture why now',
             'edition_fixture', 'journalist_fixture', 'Fixture Outlet', 'Editor Fixture',
             'Fixture angle', NULL, 'media_relations', NULL, 'Fixture metric', 'Fixture risk',
             '["constraint_fixture"]', '["signal_fixture"]', 'evidence_set_fixture',
             'pending_review', 'draft', NULL, NULL, '2026-08-14T00:00:00Z',
             '2026-08-14T00:00:00Z');
            """
        )
    finally:
        con.close()


class MigrationTests(unittest.TestCase):
    def test_migration_creates_isolated_schema_and_is_idempotent(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "pr.duckdb"

            first = apply_migrations(db, MIGRATION_DIR)
            second = apply_migrations(db, MIGRATION_DIR)
            audit = verify_schema_path(db)

        self.assertEqual(
            ["001_pr_core_media_p0", "002_pr_core_media_deletion_audit"],
            first.applied,
        )
        self.assertEqual([], first.skipped)
        self.assertEqual([], second.applied)
        self.assertEqual(
            ["001_pr_core_media_p0", "002_pr_core_media_deletion_audit"],
            second.skipped,
        )
        self.assertEqual([], audit.missing_tables)
        self.assertEqual(EXPECTED_TABLES, set(audit.present_tables))

    def test_migration_preserves_existing_main_schema_objects(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "shared.duckdb"
            con = duckdb.connect(str(db))
            con.execute("CREATE TABLE main.user_sentinel (id INTEGER PRIMARY KEY)")
            con.execute("INSERT INTO main.user_sentinel VALUES (7)")
            con.close()

            apply_migrations(db, MIGRATION_DIR)

            con = duckdb.connect(str(db), read_only=True)
            value = con.execute("SELECT id FROM main.user_sentinel").fetchone()[0]
            con.close()

        self.assertEqual(7, value)

    def test_changed_applied_migration_checksum_fails_without_mutating_database(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            db = root / "checksum.duckdb"
            migrations = root / "migrations"
            migrations.mkdir()
            for source in sorted(MIGRATION_DIR.glob("*.sql")):
                (migrations / source.name).write_bytes(source.read_bytes())
            copied = migrations / "001_pr_core_media_p0.sql"
            apply_migrations(db, migrations)

            copied.write_text(
                copied.read_text(encoding="utf-8") + "\n-- changed after apply\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                MigrationChecksumError,
                "checksum_changed.*001_pr_core_media_p0",
            ):
                apply_migrations(db, migrations)

            audit = verify_schema_path(db)

        self.assertEqual([], audit.missing_tables)

    def test_repository_rolls_back_atomic_batch_after_row_error(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "repository.duckdb"
            apply_migrations(db, MIGRATION_DIR)
            repository = PrMediaRepository(db)

            report = repository.insert_rows(
                table="dim_outlet",
                columns=(
                    "outlet_id",
                    "canonical_name",
                    "media_type",
                    "role_tags_text",
                    "status",
                    "source_file_ref",
                    "source_sheet",
                    "source_row_ref",
                    "import_version",
                    "created_at",
                    "updated_at",
                ),
                rows=(
                    (
                        "outlet_fixture_1",
                        "Fixture Outlet",
                        "review_media",
                        "review",
                        "pending",
                        "fixture.xlsx",
                        "Core",
                        "Core!2",
                        "fixture-v1",
                        "2026-08-14T00:00:00Z",
                        "2026-08-14T00:00:00Z",
                    ),
                    (
                        "outlet_fixture_1",
                        "Duplicate Primary Key",
                        "review_media",
                        "review",
                        "pending",
                        "fixture.xlsx",
                        "Core",
                        "Core!3",
                        "fixture-v1",
                        "2026-08-14T00:00:00Z",
                        "2026-08-14T00:00:00Z",
                    ),
                ),
            )

            con = duckdb.connect(str(db), read_only=True)
            count = con.execute(
                "SELECT COUNT(*) FROM pr_core_media.dim_outlet"
            ).fetchone()[0]
            con.close()

        self.assertEqual(2, report.attempted)
        self.assertEqual(0, report.inserted)
        self.assertEqual(1, len(report.errors))
        self.assertEqual(0, count)

    def test_repository_rejects_tables_outside_allowlist(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "allowlist.duckdb"
            apply_migrations(db, MIGRATION_DIR)
            repository = PrMediaRepository(db)

            with self.assertRaisesRegex(ValueError, "table_not_allowed"):
                repository.insert_rows(
                    table="main.user_data",
                    columns=("id",),
                    rows=((1,),),
                )

    def test_deletion_audit_locates_full_document_and_journalist_graph(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "lifecycle.duckdb"
            apply_migrations(db, MIGRATION_DIR)
            seed_lifecycle_graph(db)
            repository = PrMediaRepository(db)

            document_audit = locate_lifecycle_targets(
                repository, "document", "document_fixture"
            )
            journalist_audit = locate_lifecycle_targets(
                repository, "journalist", "journalist_fixture"
            )

            document_tables = {item.table_name for item in document_audit.targets}
            journalist_tables = {item.table_name for item in journalist_audit.targets}
            self.assertTrue(
                {
                    "ods_raw_envelope",
                    "dwd_document",
                    "bridge_document_byline",
                    "dwd_editorial_signal",
                    "dwd_claim",
                    "dwd_evidence",
                    "bridge_evidence_set_item",
                    "ads_media_brief",
                    "ads_opportunity",
                    "ads_media_risk",
                    "ads_action",
                }.issubset(document_tables)
            )
            self.assertTrue(
                {
                    "dim_journalist",
                    "bridge_journalist_affiliation",
                    "dim_touchpoint",
                    "dwd_document",
                    "bridge_document_byline",
                    "dwd_editorial_signal",
                    "dwd_relationship_event",
                    "dwd_pitch_constraint",
                    "dws_journalist_period",
                    "ads_media_brief",
                    "ads_opportunity",
                    "ads_media_risk",
                    "ads_action",
                }.issubset(journalist_tables)
            )
            self.assertEqual("dry_run", document_audit.status)

            con = duckdb.connect(str(db), read_only=True)
            try:
                title = con.execute(
                    "SELECT title FROM pr_core_media.dwd_document WHERE document_id = 'document_fixture'"
                ).fetchone()[0]
            finally:
                con.close()
            self.assertEqual("Sensitive Fixture Title", title)

    def test_deletion_requires_admin_confirmation_then_redacts_minimal_metadata(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "delete.duckdb"
            apply_migrations(db, MIGRATION_DIR)
            seed_lifecycle_graph(db)
            repository = PrMediaRepository(db)
            audit = locate_lifecycle_targets(
                repository, "document", "document_fixture"
            )

            with self.assertRaisesRegex(DeletionApprovalError, "admin_role_required"):
                execute_approved_deletion(
                    repository, audit.audit_id, "viewer", confirm=True
                )
            with self.assertRaisesRegex(DeletionApprovalError, "explicit_confirmation_required"):
                execute_approved_deletion(
                    repository, audit.audit_id, "admin", confirm=False
                )

            result = execute_approved_deletion(
                repository, audit.audit_id, "admin", confirm=True
            )

            self.assertEqual("completed", result.status)
            con = duckdb.connect(str(db), read_only=True)
            try:
                document = con.execute(
                    "SELECT title, author_text, deletion_status, raw_object_ref "
                    "FROM pr_core_media.dwd_document WHERE document_id = 'document_fixture'"
                ).fetchone()
                envelope = con.execute(
                    "SELECT raw_object_ref, record_count, deletion_status "
                    "FROM pr_core_media.ods_raw_envelope WHERE envelope_id = 'envelope_fixture'"
                ).fetchone()
            finally:
                con.close()
            self.assertEqual((None, None, "deleted", "deleted://document_fixture"), document)
            self.assertEqual(("deleted://envelope_fixture", 0, "deleted"), envelope)


if __name__ == "__main__":
    unittest.main()
