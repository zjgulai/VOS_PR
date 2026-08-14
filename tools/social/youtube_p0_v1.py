"""YouTube P0 V1 真实只读连接前的机器审批门。"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REQUIRED_RIGHTS = ("R1", "R4", "R5", "R6", "R17", "R18", "R19")
APPROVED_STATUSES = {"APPROVED", "APPROVED_WITH_CONDITIONS"}
FINAL_APPROVAL_STATUS = "APPROVED"
REQUIRED_SAMPLE_IDS = ("channel_id", "video_id", "reply_parent_id")


def evaluate_v1_preflight(
    record: dict[str, Any],
    *,
    environ: Mapping[str, str],
) -> dict[str, Any]:
    """评估 V1 真实只读请求是否具备审批、范围、样本和运行时条件。"""
    checks: dict[str, dict[str, Any]] = {}

    preflight = _mapping(record.get("preflight_execution"))
    preflight_ok = (
        preflight.get("status") == FINAL_APPROVAL_STATUS
        and preflight.get("scope") == "preflight_only"
        and _nonempty(preflight.get("evidence_ref"))
    )
    checks["preflight_execution"] = _check(
        preflight_ok,
        scope=preflight.get("scope"),
        evidence_present=_nonempty(preflight.get("evidence_ref")),
    )

    rights = _mapping(record.get("rights"))
    rights_evidence = _mapping(record.get("rights_evidence"))
    rights_conditions = _mapping(record.get("rights_conditions"))
    pending_rights = [
        right for right in REQUIRED_RIGHTS if rights.get(right) not in APPROVED_STATUSES
    ]
    missing_evidence_rights = [
        right for right in REQUIRED_RIGHTS if not _nonempty(rights_evidence.get(right))
    ]
    unsatisfied_condition_rights = [
        right
        for right in REQUIRED_RIGHTS
        if rights.get(right) == "APPROVED_WITH_CONDITIONS"
        and rights_conditions.get(right) is not True
    ]
    checks["rights"] = _check(
        not pending_rights
        and not missing_evidence_rights
        and not unsatisfied_condition_rights,
        pending_rights=pending_rights,
        missing_evidence_rights=missing_evidence_rights,
        unsatisfied_condition_rights=unsatisfied_condition_rights,
    )

    source_scope = _mapping(record.get("source_scope"))
    source_scope_ok = (
        source_scope.get("status") == FINAL_APPROVAL_STATUS
        and _nonempty(source_scope.get("scope_id"))
        and _nonempty(source_scope.get("scope_version"))
        and _nonempty(source_scope.get("evidence_ref"))
    )
    checks["source_scope"] = _check(
        source_scope_ok,
        approval_status=source_scope.get("status"),
        scope_id=source_scope.get("scope_id"),
        scope_version=source_scope.get("scope_version"),
        evidence_present=_nonempty(source_scope.get("evidence_ref")),
    )

    live_approval = _mapping(record.get("live_readonly_approval"))
    checks["live_readonly_approval"] = _check(
        live_approval.get("status") == FINAL_APPROVAL_STATUS
        and _nonempty(live_approval.get("evidence_ref")),
        approval_status=live_approval.get("status"),
        evidence_present=_nonempty(live_approval.get("evidence_ref")),
    )

    runtime = _mapping(record.get("runtime_environment"))
    runtime_ok = (
        runtime.get("status") == FINAL_APPROVAL_STATUS
        and _nonempty(runtime.get("name"))
        and _nonempty(runtime.get("evidence_ref"))
    )
    checks["runtime_environment"] = _check(
        runtime_ok,
        approval_status=runtime.get("status"),
        name=runtime.get("name"),
        evidence_present=_nonempty(runtime.get("evidence_ref")),
    )

    samples = _mapping(record.get("samples"))
    missing_sample_ids = [
        field for field in REQUIRED_SAMPLE_IDS if not _nonempty(samples.get(field))
    ]
    checks["sample_ids"] = _check(
        not missing_sample_ids,
        missing_fields=missing_sample_ids,
    )

    secret_source = _mapping(record.get("secret_source"))
    env_var = secret_source.get("env_var")
    env_var_name = env_var if isinstance(env_var, str) else ""
    secret_present = bool(env_var_name and environ.get(env_var_name))
    secret_ok = (
        secret_source.get("status") == FINAL_APPROVAL_STATUS
        and secret_source.get("type") in {"runtime_injection", "secret_manager"}
        and _nonempty(secret_source.get("evidence_ref"))
        and secret_present
    )
    checks["runtime_secret"] = _check(
        secret_ok,
        approval_status=secret_source.get("status"),
        source_type=secret_source.get("type"),
        env_var=env_var_name,
        evidence_present=_nonempty(secret_source.get("evidence_ref")),
        present=secret_present,
    )

    ready = all(check["status"] == "PASS" for check in checks.values())
    return {
        "record_version": record.get("record_version"),
        "overall_status": "READY" if ready else "NO_GO",
        "live_request_allowed": ready,
        "checks": checks,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check(passed: bool, **detail: Any) -> dict[str, Any]:
    return {"status": "PASS" if passed else "FAIL", **detail}
