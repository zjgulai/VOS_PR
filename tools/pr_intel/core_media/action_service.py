"""Internal-only PR Action drafts and an auditable approval/execution state machine."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Optional

from tools.pr_intel.core_media.brief_generator import MediaBrief
from tools.pr_intel.core_media.contracts import stable_id


_ACTION_TYPES = frozenset(
    {
        "media_pitch",
        "product_seeding",
        "expert_engagement",
        "topic_entry",
        "risk_response",
    }
)
_REVIEW_ROLES = frozenset(
    {"pr_analyst", "pr_lead", "brand_lead", "legal", "product_safety", "admin"}
)
_EXECUTION_ROLES = frozenset(
    {"media_relations", "media_relations_lead", "pr_lead", "admin"}
)


class InvalidTransition(ValueError):
    """Raised when an Action state transition violates the P0 approval contract."""


def _iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("action_datetime_timezone_required")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class ActionProposal:
    action_type: str
    title: str
    why_now: str
    target_outlet_text: str
    target_journalist_text: Optional[str]
    content_angle: str
    required_assets: tuple[str, ...]
    owner_role: str
    due_at: Optional[datetime]
    success_metric: str
    risk_text: str
    source_insight_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.action_type not in _ACTION_TYPES:
            raise ValueError("action_type_invalid")
        required = (
            self.title,
            self.why_now,
            self.target_outlet_text,
            self.content_angle,
            self.owner_role,
            self.success_metric,
            self.risk_text,
        )
        if not all(item.strip() for item in required):
            raise ValueError("action_required_field_missing")
        if not self.source_insight_ids:
            raise ValueError("action_source_insight_required")
        if self.due_at is not None:
            _iso(self.due_at)


@dataclass(frozen=True)
class ActionTransition:
    transition_id: str
    action_id: str
    command: str
    from_approval_status: str
    to_approval_status: str
    from_execution_status: str
    to_execution_status: str
    actor_role: str
    note: Optional[str]
    occurred_at: str


@dataclass(frozen=True)
class PrAction:
    version: str
    action_id: str
    action_type: str
    title: str
    why_now: str
    edition_id: str
    journalist_id: Optional[str]
    target_outlet_text: str
    target_journalist_text: Optional[str]
    content_angle: str
    required_assets: tuple[str, ...]
    owner_role: str
    due_at: Optional[str]
    success_metric: str
    risk_text: str
    pitch_constraint_ids: tuple[str, ...]
    source_insight_ids: tuple[str, ...]
    evidence_set_id: str
    approval_status: str
    execution_status: str
    reviewer_note: Optional[str]
    result_note: Optional[str]
    approved_by_role: Optional[str]
    approved_at: Optional[str]
    transition_history: tuple[ActionTransition, ...]
    created_at: str
    updated_at: str


def create_action_draft(brief: MediaBrief, proposal: ActionProposal) -> PrAction:
    if brief.review_status not in {"draft", "review", "approved"}:
        raise ValueError("brief_not_actionable")
    journalist_id = brief.journalist_id if brief.scope_type == "journalist" else None
    if journalist_id is None and proposal.target_journalist_text:
        raise ValueError("unverified_target_journalist_not_allowed")
    approval_status = (
        "blocked" if brief.pitch_readiness in {"blocked", "cooldown"} else "pending"
    )
    action_id = stable_id(
        "action",
        brief.brief_id,
        proposal.action_type,
        proposal.title,
        proposal.content_angle,
        proposal.owner_role,
        *proposal.source_insight_ids,
    )
    return PrAction(
        version="1.0",
        action_id=action_id,
        action_type=proposal.action_type,
        title=proposal.title,
        why_now=proposal.why_now,
        edition_id=brief.edition_id,
        journalist_id=journalist_id,
        target_outlet_text=proposal.target_outlet_text,
        target_journalist_text=proposal.target_journalist_text,
        content_angle=proposal.content_angle,
        required_assets=proposal.required_assets,
        owner_role=proposal.owner_role,
        due_at=_iso(proposal.due_at) if proposal.due_at else None,
        success_metric=proposal.success_metric,
        risk_text=proposal.risk_text,
        pitch_constraint_ids=brief.pitch_constraint_ids,
        source_insight_ids=tuple(sorted(set(proposal.source_insight_ids))),
        evidence_set_id=brief.evidence_set_id,
        approval_status=approval_status,
        execution_status="not_started",
        reviewer_note=None,
        result_note=None,
        approved_by_role=None,
        approved_at=None,
        transition_history=(),
        created_at=brief.generated_at,
        updated_at=brief.generated_at,
    )


def _authorize(command: str, actor_role: str) -> None:
    if command in {"approve", "reject", "block", "expire"}:
        if actor_role not in _REVIEW_ROLES:
            raise InvalidTransition("review_role_required")
    elif command in {"start", "complete", "cancel"}:
        if actor_role not in _EXECUTION_ROLES:
            raise InvalidTransition("execution_role_required")


def transition_action(
    action: PrAction,
    command: str,
    actor_role: str,
    *,
    note: Optional[str] = None,
    occurred_at: Optional[datetime] = None,
) -> PrAction:
    if command not in {
        "approve",
        "reject",
        "block",
        "expire",
        "start",
        "complete",
        "cancel",
    }:
        raise InvalidTransition("command_invalid")
    _authorize(command, actor_role)
    timestamp = _iso(occurred_at or datetime.now(timezone.utc))
    from_approval = action.approval_status
    from_execution = action.execution_status
    approval = from_approval
    execution = from_execution
    reviewer_note = action.reviewer_note
    result_note = action.result_note
    approved_by = action.approved_by_role
    approved_at = action.approved_at

    if command in {"approve", "reject", "block", "expire"}:
        if from_approval != "pending":
            raise InvalidTransition("approval_state_terminal")
        if command in {"reject", "block"} and not (note or "").strip():
            raise InvalidTransition("review_note_required")
        approval = {
            "approve": "approved",
            "reject": "rejected",
            "block": "blocked",
            "expire": "expired",
        }[command]
        reviewer_note = note
        if command == "approve":
            approved_by = actor_role
            approved_at = timestamp
    elif command == "start":
        if from_approval != "approved":
            raise InvalidTransition("approval_required")
        if from_execution != "not_started":
            raise InvalidTransition("execution_not_startable")
        execution = "in_progress"
    elif command in {"complete", "cancel"}:
        if from_approval != "approved":
            raise InvalidTransition("approval_required")
        if from_execution != "in_progress":
            raise InvalidTransition("execution_not_in_progress")
        if not (note or "").strip():
            raise InvalidTransition("result_note_required")
        execution = "done" if command == "complete" else "cancelled"
        result_note = note

    transition = ActionTransition(
        transition_id=stable_id(
            "action_transition",
            action.action_id,
            str(len(action.transition_history) + 1),
            command,
            timestamp,
        ),
        action_id=action.action_id,
        command=command,
        from_approval_status=from_approval,
        to_approval_status=approval,
        from_execution_status=from_execution,
        to_execution_status=execution,
        actor_role=actor_role,
        note=note,
        occurred_at=timestamp,
    )
    return replace(
        action,
        approval_status=approval,
        execution_status=execution,
        reviewer_note=reviewer_note,
        result_note=result_note,
        approved_by_role=approved_by,
        approved_at=approved_at,
        transition_history=(*action.transition_history, transition),
        updated_at=timestamp,
    )
