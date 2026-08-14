"""Atomic DuckDB writes scoped to the isolated PR core media schema."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import duckdb

from tools.etl.apply_pr_core_media_migrations import EXPECTED_TABLES


_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_WRITABLE_TABLES = EXPECTED_TABLES - {"schema_migrations"}


@dataclass(frozen=True)
class WriteError:
    code: str
    message: str


@dataclass(frozen=True)
class WriteReport:
    attempted: int
    inserted: int
    updated: int
    skipped: int
    errors: tuple[WriteError, ...]


@dataclass(frozen=True)
class TableWriteBatch:
    table: str
    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]


class PrMediaRepository:
    """Minimal repository boundary; domain-specific methods build on insert_rows."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.is_file():
            raise FileNotFoundError(f"database_not_found: {self.db_path}")

    def insert_rows(
        self,
        *,
        table: str,
        columns: Sequence[str],
        rows: Sequence[Sequence[object]],
    ) -> WriteReport:
        return self.insert_table_batches(
            (
                TableWriteBatch(
                    table=table,
                    columns=tuple(columns),
                    rows=tuple(tuple(row) for row in rows),
                ),
            )
        )

    def insert_table_batches(
        self,
        batches: Sequence[TableWriteBatch],
    ) -> WriteReport:
        materialized_batches = tuple(batches)
        for batch in materialized_batches:
            if batch.table not in _WRITABLE_TABLES:
                raise ValueError(f"table_not_allowed: {batch.table}")
            if not batch.columns or any(
                not _IDENTIFIER_RE.fullmatch(column) for column in batch.columns
            ):
                raise ValueError("columns_invalid")
            if len(set(batch.columns)) != len(batch.columns):
                raise ValueError("columns_must_be_unique")
            if any(len(row) != len(batch.columns) for row in batch.rows):
                raise ValueError("row_width_mismatch")

        attempted = sum(len(batch.rows) for batch in materialized_batches)
        if attempted == 0:
            return WriteReport(0, 0, 0, 0, ())

        con = duckdb.connect(str(self.db_path))
        try:
            con.execute("BEGIN TRANSACTION")
            try:
                for batch in materialized_batches:
                    if not batch.rows:
                        continue
                    placeholders = ", ".join("?" for _ in batch.columns)
                    column_sql = ", ".join(batch.columns)
                    sql = (
                        f"INSERT INTO pr_core_media.{batch.table} "
                        f"({column_sql}) VALUES ({placeholders})"
                    )
                    con.executemany(sql, batch.rows)
                con.execute("COMMIT")
            except Exception as exc:
                con.execute("ROLLBACK")
                return WriteReport(
                    attempted=attempted,
                    inserted=0,
                    updated=0,
                    skipped=0,
                    errors=(
                        WriteError(
                            code="duckdb_write_failed",
                            message=(
                                "Database write failed and the transaction was rolled back "
                                f"({type(exc).__name__})"
                            ),
                        ),
                    ),
                )
        finally:
            con.close()

        return WriteReport(
            attempted=attempted,
            inserted=attempted,
            updated=0,
            skipped=0,
            errors=(),
        )
