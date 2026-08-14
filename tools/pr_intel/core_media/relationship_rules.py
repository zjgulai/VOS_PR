"""Auditable relationship constraints and pitch-readiness gates."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Sequence

from tools.pr_intel.core_media.contracts import stable_id


_EVENT_TYPES = frozenset(
    {
        "pitch_sent",
        "reply_received",
        "sample_sent",
        "published",
        "declined",
        "no_reply",
        "relationship_note",
        "do_not_contact",
    }
)
_REASON_ORDER = {
    "recent_contact_30d": 10,
    "same_topic_cooldown": 20,
    "do_not_contact": 30,
    "relationship_risk": 40,
    "conflict_of_interest": 50,
    "insufficient_evidence": 60,
    "coverage_gap": 70,
    "unverified_identity": 80,
    "asset_gap": 90,
    "unresolved_media_risk": 100,
    "pending_rule_approval": 110,
    "pending_constraint_review": 120,
}


def _require_aware(value: datetime, code: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(code)


def _iso(value: datetime) -> str:
    _require_aware(value, "relationship_datetime_timezone_required")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class RelationshipEvent:
    event_id: str
    journalist_id: Optional[str]
    edition_id: str
    event_type: str
    occurred_at: Optional[datetime]
    outcome: Optional[str]
    owner_role: Optional[str]
    source_type: str
    source_row_ref: Optional[str]
    review_status: str
    created_at: Optional[datetime]

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.edition_id.strip():
            raise ValueError("relationship_event_identity_required")
        if self.event_type not in _EVENT_TYPES:
            raise ValueError("relationship_event_type_invalid")
        if not self.source_type.strip():
            raise ValueError("relationship_event_source_required")
        for value in (self.occurred_at, self.created_at):
            if value is not None:
                _require_aware(value, "relationship_event_timezone_required")


@dataclass(frozen=True)
class DocumentTopic:
    document_id: str
    edition_id: str
    journalist_id: Optional[str]
    topic_key: str
    published_at: datetime

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (self.document_id, self.edition_id, self.topic_key)
        ):
            raise ValueError("document_topic_identity_required")
        _require_aware(self.published_at, "document_topic_timezone_required")


@dataclass(frozen=True)
class RelationshipRules:
    rule_version: str
    recent_contact_days: int
    same_topic_cooldown_days: int
    approval_status: str
    decision_ref: Optional[str]
    override_roles: tuple[str, ...]
    recent_contact_event_types: tuple[str, ...] = (
        "pitch_sent",
        "reply_received",
        "sample_sent",
    )

    def __post_init__(self) -> None:
        if not self.rule_version.strip():
            raise ValueError("relationship_rule_version_required")
        if self.recent_contact_days <= 0 or self.same_topic_cooldown_days <= 0:
            raise ValueError("relationship_rule_window_invalid")
        if self.approval_status not in {"approved", "pending_business_signoff"}:
            raise ValueError("relationship_rule_approval_status_invalid")
        if self.approval_status == "approved" and not (self.decision_ref or "").strip():
            raise ValueError("relationship_rule_decision_ref_required")
        if not self.override_roles:
            raise ValueError("relationship_override_roles_required")
        if any(item not in _EVENT_TYPES for item in self.recent_contact_event_types):
            raise ValueError("recent_contact_event_type_invalid")


@dataclass(frozen=True)
class PitchConstraint:
    constraint_id: str
    journalist_id: Optional[str]
    edition_id: Optional[str]
    reason_code: str
    topic_key: Optional[str]
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    status: str
    evidence_refs: tuple[str, ...]
    rule_version: str
    approved_by_role: Optional[str]
    approved_at: Optional[datetime]
    override_evidence_ref: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PitchReadinessContext:
    edition_id: str
    journalist_id: Optional[str]
    target_topic_key: str
    constraints: tuple[PitchConstraint, ...]
    evidence_sufficient: bool
    coverage_sufficient: bool
    identity_verified: bool
    asset_gap: tuple[str, ...]
    unresolved_media_risk: bool


@dataclass(frozen=True)
class PitchReadinessDecision:
    decision_id: str
    status: str
    reason_codes: tuple[str, ...]
    constraint_ids: tuple[str, ...]


@dataclass(frozen=True)
class BackfillMetric:
    eligible_events: int
    timely_events: int
    timely_rate: Optional[float]
    missing_timestamp_event_ids: tuple[str, ...]
    invalid_order_event_ids: tuple[str, ...]
    threshold_business_days: int


@dataclass(frozen=True)
class _ConstraintSpec:
    journalist_id: Optional[str]
    edition_id: str
    reason_code: str
    topic_key: Optional[str]
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    status: str
    evidence_ref: str


def _constraint_status(review_status: str, rules: RelationshipRules) -> str:
    if rules.approval_status != "approved":
        return "pending_rule_approval"
    if review_status != "verified":
        return "pending_evidence_review"
    return "active"


def derive_pitch_constraints(
    events: Sequence[RelationshipEvent],
    documents: Sequence[DocumentTopic],
    as_of: datetime,
    rules: RelationshipRules,
) -> tuple[PitchConstraint, ...]:
    _require_aware(as_of, "relationship_as_of_timezone_required")
    specs: list[_ConstraintSpec] = []
    for event in events:
        status = _constraint_status(event.review_status, rules)
        if event.event_type == "do_not_contact":
            specs.append(
                _ConstraintSpec(
                    event.journalist_id,
                    event.edition_id,
                    "do_not_contact",
                    None,
                    event.occurred_at,
                    None,
                    status,
                    event.event_id,
                )
            )
        if event.occurred_at is None or event.occurred_at > as_of:
            continue
        age = as_of - event.occurred_at
        if (
            event.event_type in rules.recent_contact_event_types
            and age <= timedelta(days=rules.recent_contact_days)
        ):
            specs.append(
                _ConstraintSpec(
                    event.journalist_id,
                    event.edition_id,
                    "recent_contact_30d",
                    None,
                    event.occurred_at,
                    event.occurred_at + timedelta(days=rules.recent_contact_days),
                    status,
                    event.event_id,
                )
            )
        if event.event_type == "relationship_note" and event.outcome in {
            "relationship_risk",
            "conflict_of_interest",
        }:
            specs.append(
                _ConstraintSpec(
                    event.journalist_id,
                    event.edition_id,
                    str(event.outcome),
                    None,
                    event.occurred_at,
                    None,
                    status,
                    event.event_id,
                )
            )

    for document in documents:
        if document.published_at > as_of:
            continue
        if as_of - document.published_at > timedelta(
            days=rules.same_topic_cooldown_days
        ):
            continue
        status = (
            "active"
            if rules.approval_status == "approved"
            else "pending_rule_approval"
        )
        specs.append(
            _ConstraintSpec(
                document.journalist_id,
                document.edition_id,
                "same_topic_cooldown",
                document.topic_key,
                document.published_at,
                document.published_at
                + timedelta(days=rules.same_topic_cooldown_days),
                status,
                document.document_id,
            )
        )

    grouped: dict[
        tuple[Optional[str], str, str, Optional[str], str], list[_ConstraintSpec]
    ] = {}
    for spec in specs:
        key = (
            spec.journalist_id,
            spec.edition_id,
            spec.reason_code,
            spec.topic_key,
            spec.status,
        )
        grouped.setdefault(key, []).append(spec)

    result: list[PitchConstraint] = []
    for key, group in grouped.items():
        journalist_id, edition_id, reason_code, topic_key, status = key
        starts = [item.starts_at for item in group if item.starts_at is not None]
        ends = [item.ends_at for item in group if item.ends_at is not None]
        evidence_refs = tuple(sorted({item.evidence_ref for item in group}))
        constraint_id = stable_id(
            "constraint",
            journalist_id or "outlet_level",
            edition_id,
            reason_code,
            topic_key or "all_topics",
            rules.rule_version,
            *evidence_refs,
        )
        result.append(
            PitchConstraint(
                constraint_id=constraint_id,
                journalist_id=journalist_id,
                edition_id=edition_id,
                reason_code=reason_code,
                topic_key=topic_key,
                starts_at=min(starts) if starts else None,
                ends_at=None if any(item.ends_at is None for item in group) else max(ends),
                status=status,
                evidence_refs=evidence_refs,
                rule_version=rules.rule_version,
                approved_by_role=None,
                approved_at=None,
                override_evidence_ref=None,
                created_at=as_of,
                updated_at=as_of,
            )
        )
    return tuple(
        sorted(
            result,
            key=lambda item: (
                _REASON_ORDER[item.reason_code],
                item.topic_key or "",
                item.constraint_id,
            ),
        )
    )


def override_pitch_constraint(
    constraint: PitchConstraint,
    *,
    approved_by_role: str,
    approved_at: datetime,
    evidence_ref: str,
    rules: RelationshipRules,
) -> PitchConstraint:
    _require_aware(approved_at, "constraint_override_timezone_required")
    if approved_by_role not in rules.override_roles:
        raise ValueError("constraint_override_role_forbidden")
    if not evidence_ref.strip():
        raise ValueError("constraint_override_evidence_required")
    if constraint.rule_version != rules.rule_version:
        raise ValueError("constraint_rule_version_mismatch")
    return replace(
        constraint,
        status="overridden",
        approved_by_role=approved_by_role,
        approved_at=approved_at,
        override_evidence_ref=evidence_ref,
        updated_at=approved_at,
    )


def _relevant_constraints(
    context: PitchReadinessContext,
) -> tuple[PitchConstraint, ...]:
    return tuple(
        item
        for item in context.constraints
        if item.status != "overridden"
        and (item.edition_id is None or item.edition_id == context.edition_id)
        and (
            item.journalist_id is None
            or item.journalist_id == context.journalist_id
        )
        and (item.topic_key is None or item.topic_key == context.target_topic_key)
    )


def evaluate_pitch_readiness(
    context: PitchReadinessContext,
) -> PitchReadinessDecision:
    if not context.edition_id.strip() or not context.target_topic_key.strip():
        raise ValueError("pitch_readiness_identity_required")
    constraints = _relevant_constraints(context)
    active_reasons = {
        item.reason_code for item in constraints if item.status == "active"
    }
    pending_reasons: set[str] = set()
    if any(item.status == "pending_rule_approval" for item in constraints):
        pending_reasons.add("pending_rule_approval")
    if any(item.status == "pending_evidence_review" for item in constraints):
        pending_reasons.add("pending_constraint_review")

    gate_reasons: set[str] = set()
    if not context.evidence_sufficient:
        gate_reasons.add("insufficient_evidence")
    if not context.coverage_sufficient:
        gate_reasons.add("coverage_gap")
    if context.journalist_id is not None and not context.identity_verified:
        gate_reasons.add("unverified_identity")
    if context.asset_gap:
        gate_reasons.add("asset_gap")
    if context.unresolved_media_risk:
        gate_reasons.add("unresolved_media_risk")

    blocking = active_reasons & {
        "recent_contact_30d",
        "do_not_contact",
        "relationship_risk",
        "conflict_of_interest",
    }
    cooldown = active_reasons & {"same_topic_cooldown"}
    if blocking:
        status = "blocked"
        reasons = active_reasons | pending_reasons | gate_reasons
    elif cooldown:
        status = "cooldown"
        reasons = active_reasons | pending_reasons | gate_reasons
    elif pending_reasons or gate_reasons:
        status = "review_required"
        reasons = pending_reasons | gate_reasons
    else:
        status = "ready"
        reasons = set()
    reason_codes = tuple(sorted(reasons, key=lambda value: _REASON_ORDER[value]))
    constraint_ids = tuple(sorted(item.constraint_id for item in constraints))
    return PitchReadinessDecision(
        decision_id=stable_id(
            "pitch_readiness",
            context.edition_id,
            context.journalist_id or "outlet_level",
            context.target_topic_key,
            status,
            *(reason_codes or ("no_reason",)),
            *(constraint_ids or ("no_constraint",)),
        ),
        status=status,
        reason_codes=reason_codes,
        constraint_ids=constraint_ids,
    )


def _business_days_between(start: date, end: date) -> int:
    current = start
    days = 0
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days += 1
    return days


def calculate_backfill_metric(
    events: Sequence[RelationshipEvent],
    *,
    threshold_business_days: int = 3,
) -> BackfillMetric:
    if threshold_business_days <= 0:
        raise ValueError("backfill_threshold_invalid")
    eligible = 0
    timely = 0
    missing: list[str] = []
    invalid: list[str] = []
    for event in events:
        if event.occurred_at is None or event.created_at is None:
            missing.append(event.event_id)
            continue
        if event.created_at < event.occurred_at:
            invalid.append(event.event_id)
            continue
        eligible += 1
        if (
            _business_days_between(
                event.occurred_at.astimezone(timezone.utc).date(),
                event.created_at.astimezone(timezone.utc).date(),
            )
            <= threshold_business_days
        ):
            timely += 1
    return BackfillMetric(
        eligible_events=eligible,
        timely_events=timely,
        timely_rate=(timely / eligible) if eligible else None,
        missing_timestamp_event_ids=tuple(sorted(missing)),
        invalid_order_event_ids=tuple(sorted(invalid)),
        threshold_business_days=threshold_business_days,
    )
