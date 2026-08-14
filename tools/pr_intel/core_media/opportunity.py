"""Factor-preserving opportunity ranking without an unsigned composite score."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Sequence

from tools.pr_intel.core_media.contracts import stable_id


_PRESENCE_STATUSES = frozenset(
    {"observed", "not_observed_in_covered_data", "source_unavailable", "unknown"}
)
_RANK_ORDER = {
    "priority_candidate": 0,
    "review_candidate": 1,
    "insufficient_evidence": 2,
    "blocked": 3,
}


@dataclass(frozen=True)
class OpportunityContext:
    edition_id: str
    journalist_id: Optional[str]
    topic_fit: float
    timing: float
    competitor_gap: float
    momcozy_presence: str
    evidence_strength: float
    asset_gap: tuple[str, ...]
    relationship_penalty: float
    risk_penalty: float
    angle: str
    why_now: str
    evidence_set_id: str

    def __post_init__(self) -> None:
        if not self.edition_id.strip() or not self.evidence_set_id.strip():
            raise ValueError("opportunity_identity_required")
        if self.momcozy_presence not in _PRESENCE_STATUSES:
            raise ValueError("momcozy_presence_invalid")
        for name in (
            "topic_fit",
            "timing",
            "competitor_gap",
            "evidence_strength",
            "relationship_penalty",
            "risk_penalty",
        ):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f"opportunity_factor_out_of_range:{name}")
        if not self.angle.strip() or not self.why_now.strip():
            raise ValueError("opportunity_explanation_required")


@dataclass(frozen=True)
class Opportunity:
    opportunity_id: str
    edition_id: str
    journalist_id: Optional[str]
    topic_fit: float
    timing: float
    competitor_gap: float
    momcozy_presence: str
    evidence_strength: float
    asset_gap: tuple[str, ...]
    relationship_penalty: float
    risk_penalty: float
    rank_group: str
    angle: str
    why_now: str
    evidence_set_id: str
    review_status: str
    created_at: str
    updated_at: str


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("generated_at_timezone_required")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _rank_group(context: OpportunityContext) -> str:
    if context.relationship_penalty >= 0.75 or context.risk_penalty >= 0.75:
        return "blocked"
    if context.evidence_strength < 0.5:
        return "insufficient_evidence"
    if (
        context.topic_fit >= 0.7
        and context.timing >= 0.6
        and context.competitor_gap >= 0.6
        and context.evidence_strength >= 0.7
    ):
        return "priority_candidate"
    return "review_candidate"


def rank_opportunities(
    contexts: Sequence[OpportunityContext],
    *,
    generated_at: datetime,
) -> tuple[Opportunity, ...]:
    timestamp = _iso(generated_at)
    opportunities = tuple(
        Opportunity(
            opportunity_id=stable_id(
                "opportunity",
                context.edition_id,
                context.journalist_id or "outlet_level",
                context.evidence_set_id,
                context.angle,
            ),
            edition_id=context.edition_id,
            journalist_id=context.journalist_id,
            topic_fit=context.topic_fit,
            timing=context.timing,
            competitor_gap=context.competitor_gap,
            momcozy_presence=context.momcozy_presence,
            evidence_strength=context.evidence_strength,
            asset_gap=context.asset_gap,
            relationship_penalty=context.relationship_penalty,
            risk_penalty=context.risk_penalty,
            rank_group=_rank_group(context),
            angle=context.angle,
            why_now=context.why_now,
            evidence_set_id=context.evidence_set_id,
            review_status="pending_review",
            created_at=timestamp,
            updated_at=timestamp,
        )
        for context in contexts
    )
    return tuple(
        sorted(
            opportunities,
            key=lambda item: (
                _RANK_ORDER[item.rank_group],
                -item.evidence_strength,
                -item.topic_fit,
                item.opportunity_id,
            ),
        )
    )
