"""Evidence-bound, deterministic Media Brief generation for P0."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from tools.pr_intel.core_media.contracts import CoverageStatus, stable_id
from tools.pr_intel.core_media.coverage import CoverageReport
from tools.pr_intel.core_media.media_risk import MediaRiskCandidate
from tools.pr_intel.core_media.opportunity import Opportunity
from tools.pr_intel.core_media.relationship_rules import PitchReadinessDecision
from tools.pr_intel.core_media.signal_extractor import EditorialSignal, Evidence


_PRESENCE_STATUSES = frozenset(
    {"observed", "not_observed_in_covered_data", "source_unavailable", "unknown"}
)


def _iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("brief_datetime_timezone_required")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class BriefVersions:
    rule_version: str
    model_name: Optional[str]
    model_version: Optional[str]
    prompt_version: Optional[str]

    def __post_init__(self) -> None:
        if not self.rule_version.strip():
            raise ValueError("brief_rule_version_required")
        if self.model_name is None and any(
            value is not None for value in (self.model_version, self.prompt_version)
        ):
            raise ValueError("brief_model_name_required")


@dataclass(frozen=True)
class BriefContext:
    requested_scope_type: str
    requested_scope_id: str
    edition_id: str
    journalist_id: Optional[str]
    identity_verified: bool
    evidence_sufficient: bool
    window_start: datetime
    window_end: datetime
    baseline_start: Optional[datetime]
    baseline_end: Optional[datetime]
    coverage: CoverageReport
    signals: tuple[EditorialSignal, ...]
    evidence: tuple[Evidence, ...]
    opportunities: tuple[Opportunity, ...]
    media_risks: tuple[MediaRiskCandidate, ...]
    pitch_readiness: PitchReadinessDecision
    momcozy_presence_status: str
    explicit_uncertainties: tuple[str, ...]
    registry_version: str
    generated_at: datetime
    versions: BriefVersions

    def __post_init__(self) -> None:
        if self.requested_scope_type not in {"edition", "journalist"}:
            raise ValueError("brief_scope_type_invalid")
        if not all(
            value.strip()
            for value in (
                self.requested_scope_id,
                self.edition_id,
                self.registry_version,
            )
        ):
            raise ValueError("brief_scope_identity_required")
        if self.requested_scope_type == "journalist" and not self.journalist_id:
            raise ValueError("journalist_scope_id_required")
        if self.window_start >= self.window_end:
            raise ValueError("brief_window_invalid")
        _iso(self.window_start)
        _iso(self.window_end)
        _iso(self.generated_at)
        if (self.baseline_start is None) != (self.baseline_end is None):
            raise ValueError("brief_baseline_window_incomplete")
        if self.baseline_start is not None and self.baseline_end is not None:
            if self.baseline_start >= self.baseline_end:
                raise ValueError("brief_baseline_window_invalid")
            _iso(self.baseline_start)
            _iso(self.baseline_end)
        if self.momcozy_presence_status not in _PRESENCE_STATUSES:
            raise ValueError("brief_momcozy_presence_invalid")


@dataclass(frozen=True)
class FactItem:
    fact_id: str
    text: str
    signal_id: str
    evidence_ids: tuple[str, ...]
    fact_type: str = "observed_source_statement"


@dataclass(frozen=True)
class InferenceItem:
    inference_id: str
    text: str
    label: str
    evidence_set_id: str
    source_object_ids: tuple[str, ...]


@dataclass(frozen=True)
class MediaBrief:
    version: str
    brief_id: str
    scope_type: str
    scope_id: str
    edition_id: str
    journalist_id: Optional[str]
    registry_version: str
    window_start: str
    window_end: str
    baseline_start: Optional[str]
    baseline_end: Optional[str]
    actual_coverage_start: Optional[str]
    actual_coverage_end: Optional[str]
    document_count: int
    recent_focus: tuple[str, ...]
    competitor_view_ids: tuple[str, ...]
    momcozy_presence_status: str
    opportunity_ids: tuple[str, ...]
    media_risk_ids: tuple[str, ...]
    pitch_readiness: str
    no_pitch_reason_codes: tuple[str, ...]
    pitch_constraint_ids: tuple[str, ...]
    coverage_status: str
    uncertainties: tuple[str, ...]
    fact_items: tuple[FactItem, ...]
    inference_items: tuple[InferenceItem, ...]
    evidence_ids: tuple[str, ...]
    evidence_set_id: str
    rule_version: str
    model_name: Optional[str]
    model_version: Optional[str]
    prompt_version: Optional[str]
    review_status: str
    generated_at: str
    reviewed_at: Optional[str]


def _select_scope(
    context: BriefContext,
) -> tuple[str, str, Optional[str], bool]:
    if context.requested_scope_type == "edition":
        return "edition", context.edition_id, None, False
    has_journalist_evidence = any(
        signal.journalist_id == context.journalist_id for signal in context.signals
    )
    if (
        context.identity_verified
        and context.evidence_sufficient
        and has_journalist_evidence
    ):
        return "journalist", str(context.journalist_id), context.journalist_id, False
    return "edition", context.edition_id, None, True


def generate_media_brief(context: BriefContext) -> MediaBrief:
    scope_type, scope_id, journalist_id, downgraded = _select_scope(context)
    if (
        context.momcozy_presence_status == "not_observed_in_covered_data"
        and (
            context.coverage.actual_start is None
            or context.coverage.actual_end is None
        )
    ):
        raise ValueError("momcozy_gap_requires_actual_coverage")

    signals = tuple(
        signal
        for signal in context.signals
        if signal.edition_id == context.edition_id
        and (
            scope_type == "edition" or signal.journalist_id == context.journalist_id
        )
    )
    evidence_by_claim: dict[str, list[Evidence]] = {}
    for item in context.evidence:
        if item.redaction_status == "active":
            evidence_by_claim.setdefault(item.claim_id, []).append(item)

    facts: list[FactItem] = []
    used_evidence_ids: set[str] = set()
    unsupported_signal_ids: list[str] = []
    for signal in signals:
        signal_evidence = tuple(
            sorted(
                evidence_by_claim.get(signal.claim_id, ()),
                key=lambda item: item.evidence_id,
            )
        )
        if not signal_evidence:
            unsupported_signal_ids.append(signal.signal_id)
            continue
        evidence_ids = tuple(item.evidence_id for item in signal_evidence)
        used_evidence_ids.update(evidence_ids)
        facts.append(
            FactItem(
                fact_id=stable_id("brief_fact", signal.signal_id, *evidence_ids),
                text=f"Observed source statement: {signal.claim_text}",
                signal_id=signal.signal_id,
                evidence_ids=evidence_ids,
            )
        )

    opportunities = tuple(
        item
        for item in context.opportunities
        if item.edition_id == context.edition_id
        and (scope_type == "edition" or item.journalist_id == journalist_id)
    )
    media_risks = tuple(
        item
        for item in context.media_risks
        if item.edition_id == context.edition_id
        and (scope_type == "edition" or item.journalist_id == journalist_id)
    )
    inferences: list[InferenceItem] = []
    for item in opportunities:
        inferences.append(
            InferenceItem(
                inference_id=stable_id("brief_inference", item.opportunity_id),
                text=f"Opportunity analysis: {item.angle}. Why now: {item.why_now}",
                label="analysis",
                evidence_set_id=item.evidence_set_id,
                source_object_ids=(item.opportunity_id,),
            )
        )
    for item in media_risks:
        inferences.append(
            InferenceItem(
                inference_id=stable_id("brief_inference", item.media_risk_id),
                text=(
                    f"Media risk candidate analysis: {item.risk_type}; "
                    f"review status {item.review_status}"
                ),
                label="analysis",
                evidence_set_id=item.evidence_set_id,
                source_object_ids=(item.media_risk_id,),
            )
        )

    uncertainties = set(context.explicit_uncertainties)
    if downgraded:
        uncertainties.add("journalist_scope_downgraded")
    if context.coverage.status != CoverageStatus.COMPLETE:
        uncertainties.add(f"coverage_status:{context.coverage.status.value}")
    if unsupported_signal_ids:
        uncertainties.add(
            "unsupported_signals:" + ",".join(sorted(unsupported_signal_ids))
        )
    if any(item.review_status != "verified" for item in signals):
        uncertainties.add("signals_pending_human_review")
    if not facts:
        uncertainties.add("no_evidence_supported_fact_items")

    recent_focus = tuple(
        sorted({signal.topic_key for signal in signals if signal.topic_key})
    )
    competitor_view_ids = tuple(
        sorted(
            signal.signal_id
            for signal in signals
            if signal.signal_type == "competitor_view"
        )
    )
    opportunity_ids = tuple(sorted(item.opportunity_id for item in opportunities))
    media_risk_ids = tuple(sorted(item.media_risk_id for item in media_risks))
    evidence_ids = tuple(sorted(used_evidence_ids))
    evidence_set_id = stable_id(
        "brief_evidence_set",
        scope_type,
        scope_id,
        *(evidence_ids or ("no_supported_evidence",)),
    )
    generated_at = _iso(context.generated_at)
    window_start = _iso(context.window_start)
    window_end = _iso(context.window_end)
    model_version_key = context.versions.model_version or "rule_only"
    brief_id = stable_id(
        "brief",
        scope_type,
        scope_id,
        window_start,
        window_end,
        context.registry_version,
        context.versions.rule_version,
        model_version_key,
        evidence_set_id,
    )
    return MediaBrief(
        version="1.0",
        brief_id=brief_id,
        scope_type=scope_type,
        scope_id=scope_id,
        edition_id=context.edition_id,
        journalist_id=journalist_id,
        registry_version=context.registry_version,
        window_start=window_start,
        window_end=window_end,
        baseline_start=(
            _iso(context.baseline_start) if context.baseline_start else None
        ),
        baseline_end=_iso(context.baseline_end) if context.baseline_end else None,
        actual_coverage_start=context.coverage.actual_start,
        actual_coverage_end=context.coverage.actual_end,
        document_count=context.coverage.documents_accepted,
        recent_focus=recent_focus,
        competitor_view_ids=competitor_view_ids,
        momcozy_presence_status=context.momcozy_presence_status,
        opportunity_ids=opportunity_ids,
        media_risk_ids=media_risk_ids,
        pitch_readiness=context.pitch_readiness.status,
        no_pitch_reason_codes=context.pitch_readiness.reason_codes,
        pitch_constraint_ids=context.pitch_readiness.constraint_ids,
        coverage_status=context.coverage.status.value,
        uncertainties=tuple(sorted(uncertainties)),
        fact_items=tuple(sorted(facts, key=lambda item: item.fact_id)),
        inference_items=tuple(
            sorted(inferences, key=lambda item: item.inference_id)
        ),
        evidence_ids=evidence_ids,
        evidence_set_id=evidence_set_id,
        rule_version=context.versions.rule_version,
        model_name=context.versions.model_name,
        model_version=context.versions.model_version,
        prompt_version=context.versions.prompt_version,
        review_status="draft",
        generated_at=generated_at,
        reviewed_at=None,
    )
