"""Relevance-gated Media Risk candidates for P0; this is not crisis severity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tools.pr_intel.core_media.contracts import stable_id
from tools.pr_intel.core_media.normalizer import Document
from tools.pr_intel.core_media.signal_extractor import EditorialSignal


_DIRECT_HIGH_RISK_TYPES = frozenset(
    {"product_safety", "quality", "privacy", "authenticity", "legal"}
)


@dataclass(frozen=True)
class MediaRiskCandidate:
    media_risk_id: str
    document_id: str
    edition_id: str
    journalist_id: Optional[str]
    risk_type: str
    brand_relevance: str
    product_relevance: str
    category_relevance: str
    evidence_span: str
    sponsorship_status: str
    priority: str
    review_status: str
    escalation_result: Optional[str]
    evidence_set_id: str
    created_at: str
    updated_at: str


def _risk_type(signal: EditorialSignal) -> str:
    marker = "contains a "
    suffix = " risk candidate"
    folded = signal.claim_text.casefold()
    if marker in folded and suffix in folded:
        return folded.split(marker, 1)[1].split(suffix, 1)[0]
    return "reputational"


def evaluate_media_risk(
    signal: EditorialSignal,
    document: Document,
) -> MediaRiskCandidate:
    if signal.signal_type != "media_risk":
        raise ValueError("media_risk_signal_required")
    if signal.document_id != document.document_id:
        raise ValueError("media_risk_document_mismatch")
    risk_type = _risk_type(signal)
    brand_relevance = "direct" if signal.subject_entity == "momcozy" else "not_relevant"
    product_relevance = (
        "direct" if signal.subject_entity is not None else "not_relevant"
    )
    category_relevance = (
        "direct"
        if signal.topic_key and signal.topic_key != "unclassified"
        else "not_relevant"
    )
    relevance_passed = (
        bool(signal.evidence_span.strip())
        and signal.subject_entity is not None
        and (product_relevance == "direct" or category_relevance == "direct")
    )
    if not relevance_passed:
        priority = "none"
        review_status = "rejected_by_relevance_gate"
        escalation_result = "not_escalated"
    else:
        if brand_relevance == "direct" and risk_type in _DIRECT_HIGH_RISK_TYPES:
            priority = "high"
        elif category_relevance == "direct":
            priority = "medium"
        else:
            priority = "low"
        if document.sponsorship_status in {"sponsored", "affiliate", "syndicated"}:
            priority = {"high": "medium", "medium": "low", "low": "low"}[priority]
        review_status = "pending_review"
        escalation_result = "awaiting_human_review"

    return MediaRiskCandidate(
        media_risk_id=stable_id(
            "media_risk", signal.signal_id, risk_type, signal.rule_version
        ),
        document_id=document.document_id,
        edition_id=document.edition_id,
        journalist_id=signal.journalist_id,
        risk_type=risk_type,
        brand_relevance=brand_relevance,
        product_relevance=product_relevance,
        category_relevance=category_relevance,
        evidence_span=signal.evidence_span,
        sponsorship_status=document.sponsorship_status,
        priority=priority,
        review_status=review_status,
        escalation_result=escalation_result,
        evidence_set_id=signal.evidence_set_id,
        created_at=signal.created_at,
        updated_at=signal.created_at,
    )
