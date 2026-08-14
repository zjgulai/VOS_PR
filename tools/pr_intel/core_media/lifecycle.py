"""Two-step lifecycle discovery and approved redaction for PR core-media data."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Sequence

import duckdb

from tools.pr_intel.core_media.contracts import stable_id
from tools.pr_intel.core_media.storage import (
    PrMediaRepository,
    TableWriteBatch,
)


class DeletionApprovalError(RuntimeError):
    pass


@dataclass(frozen=True)
class DeletionTarget:
    target_id: str
    table_name: str
    selector_json: str
    target_action: str
    located_count: int
    execution_status: str


@dataclass(frozen=True)
class DeletionAudit:
    audit_id: str
    object_type: str
    object_id: str
    status: str
    target_count: int
    unresolved_dependencies: tuple[str, ...]
    targets: tuple[DeletionTarget, ...]
    created_at: str


@dataclass(frozen=True)
class DeletionResult:
    audit_id: str
    status: str
    targets_executed: int
    rows_affected: int
    completed_at: str


@dataclass(frozen=True)
class _TargetSpec:
    table_name: str
    selector_json: str
    target_action: str
    located_count: int


_SELECTOR_COLUMNS = {
    "dim_journalist": {"journalist_id"},
    "bridge_journalist_affiliation": {"journalist_id"},
    "dim_touchpoint": {"entity_type", "entity_id"},
    "ods_raw_envelope": {"envelope_id", "raw_object_ref"},
    "dwd_document": {"document_id", "journalist_id"},
    "bridge_document_byline": {"document_id", "journalist_id"},
    "dwd_editorial_signal": {"document_id", "journalist_id", "signal_id"},
    "dwd_claim": {"claim_id"},
    "dwd_evidence": {"evidence_id", "document_id", "claim_id"},
    "bridge_evidence_set_item": {"evidence_id", "evidence_set_id"},
    "dwd_relationship_event": {"journalist_id"},
    "dwd_pitch_constraint": {"journalist_id"},
    "dws_journalist_period": {"journalist_id"},
    "ads_media_brief": {"brief_id", "scope_type", "scope_id", "evidence_set_id"},
    "ads_opportunity": {"opportunity_id", "journalist_id", "evidence_set_id"},
    "ads_media_risk": {"media_risk_id", "document_id", "journalist_id", "evidence_set_id"},
    "ads_action": {"action_id", "journalist_id", "evidence_set_id"},
    "ctl_action_transition": {"action_id", "transition_id"},
    "ctl_brief_review": {"brief_id", "review_id"},
}

_EXECUTION_ORDER = {
    "ctl_action_transition": 5,
    "ads_action": 10,
    "ads_opportunity": 20,
    "ads_media_risk": 30,
    "ctl_brief_review": 35,
    "ads_media_brief": 40,
    "bridge_evidence_set_item": 50,
    "dwd_evidence": 60,
    "dwd_claim": 70,
    "dwd_editorial_signal": 80,
    "bridge_document_byline": 90,
    "dws_journalist_period": 100,
    "dwd_relationship_event": 110,
    "dwd_pitch_constraint": 120,
    "dim_touchpoint": 130,
    "bridge_journalist_affiliation": 140,
    "dwd_document": 150,
    "ods_raw_envelope": 160,
    "dim_journalist": 170,
}


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _selector_json(selector: dict[str, str]) -> str:
    return json.dumps(selector, sort_keys=True, separators=(",", ":"))


def _where(table: str, selector: dict[str, str]) -> tuple[str, list[str]]:
    allowed = _SELECTOR_COLUMNS.get(table)
    if allowed is None or not selector or not set(selector).issubset(allowed):
        raise ValueError("lifecycle_selector_not_allowed")
    columns = sorted(selector)
    clause = " AND ".join(f"{column} = ?" for column in columns)
    return clause, [selector[column] for column in columns]


def _count(
    con: duckdb.DuckDBPyConnection,
    table: str,
    selector: dict[str, str],
) -> int:
    clause, values = _where(table, selector)
    return int(
        con.execute(
            f"SELECT count(*) FROM pr_core_media.{table} WHERE {clause}", values
        ).fetchone()[0]
    )


def _add(
    con: duckdb.DuckDBPyConnection,
    targets: list[_TargetSpec],
    table: str,
    selector: dict[str, str],
    action: str,
) -> None:
    count = _count(con, table, selector)
    if count == 0:
        return
    serialized = _selector_json(selector)
    key = (table, serialized, action)
    if any((item.table_name, item.selector_json, item.target_action) == key for item in targets):
        return
    targets.append(_TargetSpec(table, serialized, action, count))


def _add_deleted_action(
    con: duckdb.DuckDBPyConnection,
    targets: list[_TargetSpec],
    action_id: str,
) -> None:
    _add(
        con,
        targets,
        "ctl_action_transition",
        {"action_id": action_id},
        "delete_row",
    )
    _add(con, targets, "ads_action", {"action_id": action_id}, "delete_row")


def _add_deleted_brief(
    con: duckdb.DuckDBPyConnection,
    targets: list[_TargetSpec],
    brief_id: str,
) -> None:
    _add(
        con,
        targets,
        "ctl_brief_review",
        {"brief_id": brief_id},
        "delete_row",
    )
    _add(con, targets, "ads_media_brief", {"brief_id": brief_id}, "delete_row")


def _document_targets(
    con: duckdb.DuckDBPyConnection,
    document_id: str,
) -> list[_TargetSpec]:
    row = con.execute(
        "SELECT raw_object_ref FROM pr_core_media.dwd_document WHERE document_id = ?",
        [document_id],
    ).fetchone()
    if row is None:
        raise ValueError("lifecycle_object_not_found")

    targets: list[_TargetSpec] = []
    evidence_rows = con.execute(
        "SELECT evidence_id, claim_id FROM pr_core_media.dwd_evidence WHERE document_id = ?",
        [document_id],
    ).fetchall()
    signal_rows = con.execute(
        "SELECT signal_id, evidence_set_id FROM pr_core_media.dwd_editorial_signal WHERE document_id = ?",
        [document_id],
    ).fetchall()
    evidence_ids = [str(item[0]) for item in evidence_rows]
    claim_ids = [str(item[1]) for item in evidence_rows]
    evidence_set_ids = {str(item[1]) for item in signal_rows if item[1]}
    for evidence_id in evidence_ids:
        rows = con.execute(
            "SELECT evidence_set_id FROM pr_core_media.bridge_evidence_set_item WHERE evidence_id = ?",
            [evidence_id],
        ).fetchall()
        evidence_set_ids.update(str(item[0]) for item in rows)

    _add(con, targets, "ads_media_risk", {"document_id": document_id}, "delete_row")
    for evidence_set_id in sorted(evidence_set_ids):
        brief_rows = con.execute(
            "SELECT brief_id FROM pr_core_media.ads_media_brief WHERE evidence_set_id = ?",
            [evidence_set_id],
        ).fetchall()
        for brief_row in brief_rows:
            _add_deleted_brief(con, targets, str(brief_row[0]))
        _add(
            con,
            targets,
            "ads_opportunity",
            {"evidence_set_id": evidence_set_id},
            "delete_row",
        )
        action_rows = con.execute(
            "SELECT action_id FROM pr_core_media.ads_action WHERE evidence_set_id = ?",
            [evidence_set_id],
        ).fetchall()
        for action_row in action_rows:
            _add_deleted_action(con, targets, str(action_row[0]))
    for signal_id, _ in signal_rows:
        action_rows = con.execute(
            "SELECT action_id FROM pr_core_media.ads_action "
            "WHERE strpos(source_insight_ids_text, ?) > 0",
            [str(signal_id)],
        ).fetchall()
        for action_row in action_rows:
            _add_deleted_action(con, targets, str(action_row[0]))

    for evidence_id in evidence_ids:
        _add(
            con,
            targets,
            "bridge_evidence_set_item",
            {"evidence_id": evidence_id},
            "delete_row",
        )
    _add(
        con,
        targets,
        "dwd_evidence",
        {"document_id": document_id},
        "delete_row",
    )
    for claim_id in sorted(set(claim_ids)):
        other_evidence = int(
            con.execute(
                "SELECT count(*) FROM pr_core_media.dwd_evidence "
                "WHERE claim_id = ? AND document_id <> ?",
                [claim_id, document_id],
            ).fetchone()[0]
        )
        if other_evidence == 0:
            _add(
                con,
                targets,
                "dwd_claim",
                {"claim_id": claim_id},
                "redact_claim",
            )
    _add(
        con,
        targets,
        "dwd_editorial_signal",
        {"document_id": document_id},
        "delete_row",
    )
    _add(
        con,
        targets,
        "bridge_document_byline",
        {"document_id": document_id},
        "delete_row",
    )
    _add(
        con,
        targets,
        "dwd_document",
        {"document_id": document_id},
        "redact_document",
    )
    _add(
        con,
        targets,
        "ods_raw_envelope",
        {"raw_object_ref": str(row[0])},
        "redact_raw_envelope",
    )
    return targets


def _journalist_targets(
    con: duckdb.DuckDBPyConnection,
    journalist_id: str,
) -> list[_TargetSpec]:
    if _count(con, "dim_journalist", {"journalist_id": journalist_id}) == 0:
        raise ValueError("lifecycle_object_not_found")
    targets: list[_TargetSpec] = []
    _add(con, targets, "ads_action", {"journalist_id": journalist_id}, "redact_journalist_link")
    _add(con, targets, "ads_opportunity", {"journalist_id": journalist_id}, "redact_journalist_link")
    _add(con, targets, "ads_media_risk", {"journalist_id": journalist_id}, "redact_journalist_link")
    brief_rows = con.execute(
        "SELECT brief_id FROM pr_core_media.ads_media_brief "
        "WHERE scope_type = 'journalist' AND scope_id = ?",
        [journalist_id],
    ).fetchall()
    for brief_row in brief_rows:
        _add_deleted_brief(con, targets, str(brief_row[0]))
    _add(con, targets, "dws_journalist_period", {"journalist_id": journalist_id}, "delete_row")
    _add(con, targets, "dwd_relationship_event", {"journalist_id": journalist_id}, "delete_row")
    _add(con, targets, "dwd_pitch_constraint", {"journalist_id": journalist_id}, "delete_row")
    _add(con, targets, "dwd_editorial_signal", {"journalist_id": journalist_id}, "redact_journalist_link")
    _add(con, targets, "bridge_document_byline", {"journalist_id": journalist_id}, "delete_row")
    _add(con, targets, "dwd_document", {"journalist_id": journalist_id}, "redact_journalist_link")
    _add(
        con,
        targets,
        "dim_touchpoint",
        {"entity_type": "journalist", "entity_id": journalist_id},
        "delete_row",
    )
    _add(
        con,
        targets,
        "bridge_journalist_affiliation",
        {"journalist_id": journalist_id},
        "delete_row",
    )
    _add(con, targets, "dim_journalist", {"journalist_id": journalist_id}, "redact_journalist")
    return targets


def locate_lifecycle_targets(
    repository: PrMediaRepository,
    object_type: str,
    object_id: str,
    *,
    requested_by_role: str = "data_governance",
    reason_code: str = "privacy_or_removal_request",
) -> DeletionAudit:
    if object_type not in {"document", "journalist"}:
        raise ValueError("lifecycle_object_type_invalid")
    if not object_id.strip():
        raise ValueError("lifecycle_object_id_required")
    con = duckdb.connect(str(repository.db_path), read_only=True)
    try:
        specs = (
            _document_targets(con, object_id)
            if object_type == "document"
            else _journalist_targets(con, object_id)
        )
    finally:
        con.close()

    created_at = _now()
    audit_id = stable_id(
        "deletion_audit", object_type, object_id, created_at, uuid.uuid4().hex
    )
    targets = tuple(
        DeletionTarget(
            target_id=stable_id(
                "deletion_target",
                audit_id,
                spec.table_name,
                spec.selector_json,
                spec.target_action,
            ),
            table_name=spec.table_name,
            selector_json=spec.selector_json,
            target_action=spec.target_action,
            located_count=spec.located_count,
            execution_status="pending",
        )
        for spec in specs
    )
    report = repository.insert_table_batches(
        (
            TableWriteBatch(
                "ctl_deletion_audit",
                (
                    "audit_id",
                    "object_type",
                    "object_id",
                    "requested_by_role",
                    "reason_code",
                    "status",
                    "target_count",
                    "unresolved_dependencies_text",
                    "created_at",
                ),
                ((
                    audit_id,
                    object_type,
                    object_id,
                    requested_by_role,
                    reason_code,
                    "dry_run",
                    sum(item.located_count for item in targets),
                    "[]",
                    created_at,
                ),),
            ),
            TableWriteBatch(
                "ctl_deletion_target",
                (
                    "target_id",
                    "audit_id",
                    "table_name",
                    "selector_json",
                    "target_action",
                    "located_count",
                    "execution_status",
                    "executed_count",
                    "created_at",
                ),
                tuple((
                    item.target_id,
                    audit_id,
                    item.table_name,
                    item.selector_json,
                    item.target_action,
                    item.located_count,
                    "pending",
                    0,
                    created_at,
                ) for item in targets),
            ),
        )
    )
    if report.errors:
        raise RuntimeError(report.errors[0].message)
    return DeletionAudit(
        audit_id=audit_id,
        object_type=object_type,
        object_id=object_id,
        status="dry_run",
        target_count=sum(item.located_count for item in targets),
        unresolved_dependencies=(),
        targets=targets,
        created_at=created_at,
    )


def _execute_target(
    con: duckdb.DuckDBPyConnection,
    audit_id: str,
    table: str,
    selector: dict[str, str],
    action: str,
) -> int:
    clause, values = _where(table, selector)
    before = _count(con, table, selector)
    if action == "delete_row":
        con.execute(f"DELETE FROM pr_core_media.{table} WHERE {clause}", values)
    elif action == "retain_audit_link":
        pass
    elif action == "redact_evidence":
        con.execute(
            f"UPDATE pr_core_media.dwd_evidence SET quote_span = NULL, "
            f"redaction_status = 'deleted' WHERE {clause}",
            values,
        )
    elif action == "redact_claim":
        claim_id = selector["claim_id"]
        con.execute(
            f"""
            UPDATE pr_core_media.dwd_claim
            SET claim_text = ?, claimant_text = 'deleted', subject = 'deleted',
                predicate = 'deleted', time_scope = NULL, verification_status = 'deleted',
                confidence = 0, entities_text = NULL, model_name = NULL,
                prompt_version = NULL, review_status = 'deleted'
            WHERE {clause}
            """,
            [f"deleted:{claim_id}", *values],
        )
    elif action == "redact_document":
        document_id = selector["document_id"]
        con.execute(
            f"""
            UPDATE pr_core_media.dwd_document
            SET canonical_url = ?, journalist_id = NULL, title = NULL, author_text = NULL,
                byline_status = 'no_byline', content_type = 'unknown',
                sponsorship_status = 'unknown', text_hash = ?, rights_label = 'metadata_only',
                is_syndicated = false, canonical_document_id = NULL,
                deletion_status = 'deleted', raw_object_ref = ?, updated_at = current_timestamp
            WHERE {clause}
            """,
            [
                f"deleted://{document_id}",
                f"deleted:{audit_id}",
                f"deleted://{document_id}",
                *values,
            ],
        )
    elif action == "redact_raw_envelope":
        rows = con.execute(
            f"SELECT envelope_id FROM pr_core_media.ods_raw_envelope WHERE {clause}",
            values,
        ).fetchall()
        for row in rows:
            con.execute(
                """
                UPDATE pr_core_media.ods_raw_envelope
                SET raw_object_ref = ?, allowed_fields_text = '[]', record_count = 0,
                    deletion_status = 'deleted'
                WHERE envelope_id = ?
                """,
                [f"deleted://{row[0]}", str(row[0])],
            )
    elif action == "redact_journalist":
        journalist_id = selector["journalist_id"]
        con.execute(
            f"""
            UPDATE pr_core_media.dim_journalist
            SET public_name = ?, public_title = NULL, identity_status = 'deleted',
                verified_at = NULL, verification_evidence_ref = NULL,
                updated_at = current_timestamp
            WHERE {clause}
            """,
            [f"deleted:{journalist_id}", *values],
        )
    elif action == "redact_journalist_link":
        if table == "dwd_document":
            con.execute(
                f"UPDATE pr_core_media.dwd_document SET journalist_id = NULL, "
                f"author_text = NULL, byline_status = 'unverified', updated_at = current_timestamp "
                f"WHERE {clause}",
                values,
            )
        elif table == "dwd_editorial_signal":
            con.execute(
                f"UPDATE pr_core_media.dwd_editorial_signal SET journalist_id = NULL "
                f"WHERE {clause}",
                values,
            )
        elif table in {"ads_opportunity", "ads_media_risk"}:
            con.execute(
                f"UPDATE pr_core_media.{table} SET journalist_id = NULL WHERE {clause}",
                values,
            )
        elif table == "ads_action":
            con.execute(
                f"UPDATE pr_core_media.ads_action SET journalist_id = NULL, "
                f"target_journalist_text = NULL, updated_at = current_timestamp "
                f"WHERE {clause}",
                values,
            )
        else:
            raise ValueError("redact_journalist_link_table_invalid")
    else:
        raise ValueError("lifecycle_action_invalid")
    return before


def execute_approved_deletion(
    repository: PrMediaRepository,
    audit_id: str,
    approved_by_role: str,
    *,
    confirm: bool,
) -> DeletionResult:
    if approved_by_role.strip().casefold() != "admin":
        raise DeletionApprovalError("admin_role_required")
    if not confirm:
        raise DeletionApprovalError("explicit_confirmation_required")

    con = duckdb.connect(str(repository.db_path))
    try:
        audit_row = con.execute(
            "SELECT status, unresolved_dependencies_text FROM pr_core_media.ctl_deletion_audit "
            "WHERE audit_id = ?",
            [audit_id],
        ).fetchone()
        if audit_row is None:
            raise DeletionApprovalError("deletion_audit_not_found")
        if audit_row[0] not in {"dry_run", "executing", "execution_failed"}:
            raise DeletionApprovalError("deletion_audit_not_executable")
        if json.loads(str(audit_row[1])):
            raise DeletionApprovalError("unresolved_dependencies_present")
        if audit_row[0] == "dry_run":
            con.execute(
                """
                UPDATE pr_core_media.ctl_deletion_audit
                SET status = 'executing', approved_by_role = ?,
                    approved_at = current_timestamp, safe_error_message = NULL
                WHERE audit_id = ?
                """,
                ["admin", audit_id],
            )
        else:
            con.execute(
                """
                UPDATE pr_core_media.ctl_deletion_audit
                SET status = 'executing', safe_error_message = NULL
                WHERE audit_id = ?
                """,
                [audit_id],
            )
        rows = con.execute(
            """
            SELECT target_id, table_name, selector_json, target_action, located_count
            FROM pr_core_media.ctl_deletion_target
            WHERE audit_id = ? AND execution_status = 'pending'
            """,
            [audit_id],
        ).fetchall()
        ordered = sorted(rows, key=lambda row: _EXECUTION_ORDER[str(row[1])])
        total = 0
        completed_targets = 0
        for target_id, table, selector_json, action, located_count in ordered:
            con.execute("BEGIN TRANSACTION")
            try:
                selector = json.loads(str(selector_json))
                if _count(con, str(table), selector) != int(located_count):
                    raise RuntimeError(
                        f"deletion_target_drift:{table}:{target_id}"
                    )
                try:
                    affected = _execute_target(
                        con, audit_id, str(table), selector, str(action)
                    )
                except Exception as exc:
                    raise RuntimeError(
                        f"deletion_execution_failed:{table}:{type(exc).__name__}"
                    ) from exc
                total += affected
                completed_targets += 1
                con.execute(
                    """
                    UPDATE pr_core_media.ctl_deletion_target
                    SET execution_status = 'completed', executed_count = ?,
                        executed_at = current_timestamp
                    WHERE target_id = ?
                    """,
                    [affected, str(target_id)],
                )
                con.execute("COMMIT")
            except Exception as exc:
                con.execute("ROLLBACK")
                safe_error = f"deletion_execution_failed:{table}:{type(exc).__name__}"
                con.execute(
                    """
                    UPDATE pr_core_media.ctl_deletion_audit
                    SET status = 'execution_failed', safe_error_message = ?
                    WHERE audit_id = ?
                    """,
                    [safe_error, audit_id],
                )
                if isinstance(exc, RuntimeError) and str(exc).startswith(
                    "deletion_target_drift:"
                ):
                    raise
                raise RuntimeError(safe_error) from exc

        con.execute("BEGIN TRANSACTION")
        try:
            con.execute(
                """
                UPDATE pr_core_media.ctl_deletion_audit
                SET status = 'completed', completed_at = current_timestamp
                WHERE audit_id = ?
                """,
                [audit_id],
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    finally:
        con.close()

    completed_at = _now()
    return DeletionResult(
        audit_id=audit_id,
        status="completed",
        targets_executed=completed_targets,
        rows_affected=total,
        completed_at=completed_at,
    )
