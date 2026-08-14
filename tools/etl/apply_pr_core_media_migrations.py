"""Apply checksum-protected DuckDB migrations for PR core media P0."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MIGRATION_DIR = Path(__file__).resolve().parent / "migrations" / "pr_core_media"

EXPECTED_TABLES = frozenset(
    {
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
        "ctl_action_transition",
        "ctl_brief_review",
        "ctl_deletion_audit",
        "ctl_deletion_target",
    }
)


class MigrationChecksumError(RuntimeError):
    """Raised when an already-applied migration file has changed."""


@dataclass(frozen=True)
class MigrationReport:
    db_path: str
    migration_dir: str
    applied: list[str]
    skipped: list[str]


@dataclass(frozen=True)
class SchemaAudit:
    present_tables: list[str]
    missing_tables: list[str]
    unexpected_tables: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing_tables and not self.unexpected_tables


def _migration_files(migration_dir: Path) -> list[Path]:
    if not migration_dir.is_dir():
        raise FileNotFoundError(f"migration_dir_not_found: {migration_dir}")
    files = sorted(migration_dir.glob("*.sql"))
    if not files:
        raise FileNotFoundError(f"migration_files_not_found: {migration_dir}")
    return files


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_migration_registry(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS pr_core_media")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS pr_core_media.schema_migrations (
            migration_id VARCHAR PRIMARY KEY,
            checksum VARCHAR NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
        """
    )


def apply_migrations(db_path: Path, migration_dir: Path = DEFAULT_MIGRATION_DIR) -> MigrationReport:
    """Apply immutable SQL files transactionally to an explicit DuckDB path."""
    db_path = Path(db_path)
    migration_dir = Path(migration_dir)
    if str(db_path).strip() in {"", "."}:
        raise ValueError("db_path_required")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    applied: list[str] = []
    skipped: list[str] = []
    try:
        _ensure_migration_registry(con)
        for path in _migration_files(migration_dir):
            migration_id = path.stem
            checksum = _checksum(path)
            existing = con.execute(
                """
                SELECT checksum
                FROM pr_core_media.schema_migrations
                WHERE migration_id = ?
                """,
                [migration_id],
            ).fetchone()
            if existing is not None:
                if existing[0] != checksum:
                    raise MigrationChecksumError(
                        f"checksum_changed: {migration_id}"
                    )
                skipped.append(migration_id)
                continue

            con.execute("BEGIN TRANSACTION")
            try:
                con.execute(path.read_text(encoding="utf-8"))
                con.execute(
                    """
                    INSERT INTO pr_core_media.schema_migrations
                    (migration_id, checksum, applied_at)
                    VALUES (?, ?, current_timestamp)
                    """,
                    [migration_id, checksum],
                )
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
            applied.append(migration_id)
    finally:
        con.close()

    return MigrationReport(
        db_path=str(db_path),
        migration_dir=str(migration_dir),
        applied=applied,
        skipped=skipped,
    )


def verify_schema(con: duckdb.DuckDBPyConnection) -> SchemaAudit:
    rows = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'pr_core_media'
        ORDER BY table_name
        """
    ).fetchall()
    present = [str(row[0]) for row in rows]
    present_set = set(present)
    return SchemaAudit(
        present_tables=present,
        missing_tables=sorted(EXPECTED_TABLES - present_set),
        unexpected_tables=sorted(present_set - EXPECTED_TABLES),
    )


def verify_schema_path(db_path: Path) -> SchemaAudit:
    db_path = Path(db_path)
    if not db_path.is_file():
        raise FileNotFoundError(f"database_not_found: {db_path}")
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return verify_schema(con)
    finally:
        con.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply PR core media DuckDB migrations")
    parser.add_argument("--db", type=Path, required=True, help="Explicit DuckDB file path")
    parser.add_argument(
        "--migration-dir",
        type=Path,
        default=DEFAULT_MIGRATION_DIR,
        help="Directory containing immutable SQL migration files",
    )
    parser.add_argument("--verify", action="store_true", help="Verify without applying")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    if args.verify:
        report = verify_schema_path(args.db)
    else:
        report = apply_migrations(args.db, args.migration_dir)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
