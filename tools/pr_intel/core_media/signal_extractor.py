"""Deterministic, evidence-first signal extraction for the PR core-media P0."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from tools.pr_intel.core_media.contracts import stable_id
from tools.pr_intel.core_media.normalizer import Document


_PRESENCE_STATUSES = frozenset(
    {"observed", "not_observed_in_covered_data", "source_unavailable", "unknown"}
)
_POSITIVE_MARKERS = (
    "comfortable",
    "easy to use",
    "effective",
    "powerful",
    "portable",
    "quiet",
    "recommend",
    "reliable",
)
_NEGATIVE_MARKERS = (
    "clunky",
    "defect",
    "disappoint",
    "failure",
    "leak",
    "noisy",
    "unsafe",
    "uncomfortable",
    "weak",
)
_QUALITY_MARKERS = (
    "coating peeling",
    "crack",
    "defect",
    "failure",
    "leak",
    "motor failure",
    "quality",
)
_CATEGORY_MARKERS = (
    "breast pump",
    "wearable pump",
    "pumping",
)


@dataclass(frozen=True)
class CounterEvidenceInput:
    document_id: str
    quote_span: str
    observed_at: str
    evidence_grade: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.document_id,
                self.quote_span,
                self.observed_at,
                self.evidence_grade,
            )
        ):
            raise ValueError("counterevidence_provenance_required")


@dataclass(frozen=True)
class AnalysisDocument:
    """A normalized document plus only the text its rights label allows."""

    document: Document
    allowed_evidence_text: str
    counterevidence: tuple[CounterEvidenceInput, ...] = ()
    evidence_grade: str = "ungraded"

    def __post_init__(self) -> None:
        if self.document.deletion_status != "active":
            raise ValueError("deleted_document_not_analyzable")
        text = " ".join(self.allowed_evidence_text.strip().split())
        if not text:
            raise ValueError("allowed_evidence_text_required")
        if self.document.rights_label == "metadata_only":
            title = " ".join((self.document.title or "").strip().split())
            if text != title:
                raise ValueError("metadata_only_analysis_must_use_title_only")
        elif self.document.rights_label == "excerpt_only" and len(text) > 2000:
            raise ValueError("excerpt_only_analysis_text_too_long")
        elif self.document.rights_label not in {
            "excerpt_only",
            "full_text_allowed",
            "metadata_only",
        }:
            raise ValueError("analysis_rights_label_invalid")
        if not self.evidence_grade.strip():
            raise ValueError("evidence_grade_required")


@dataclass(frozen=True)
class SignalVersions:
    rule_version: str
    dictionary_version: str
    taxonomy_version: str
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.rule_version.strip():
            raise ValueError("rule_version_required")
        if self.model_name is None and any(
            value is not None for value in (self.model_version, self.prompt_version)
        ):
            raise ValueError("model_name_required_for_model_versions")


@dataclass(frozen=True)
class EditorialSignal:
    signal_id: str
    document_id: str
    edition_id: str
    journalist_id: Optional[str]
    signal_type: str
    subject_entity: Optional[str]
    topic_key: Optional[str]
    stance: str
    claim_text: str
    evidence_span: str
    sponsorship_status: str
    confidence: float
    review_status: str
    evidence_set_id: str
    claim_id: str
    rule_version: str
    model_name: Optional[str]
    model_version: Optional[str]
    prompt_version: Optional[str]
    created_at: str


@dataclass(frozen=True)
class Claim:
    claim_id: str
    claim_text: str
    claimant_text: str
    subject: str
    predicate: str
    time_scope: Optional[str]
    verification_status: str
    evidence_ids: tuple[str, ...]
    counterevidence_ids: tuple[str, ...]
    confidence: float
    markets: tuple[str, ...]
    entities: tuple[str, ...]
    model_name: Optional[str]
    model_version: str
    prompt_version: Optional[str]
    review_status: str
    created_at: str


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    claim_id: str
    document_id: str
    quote_span: str
    supports_or_refutes: str
    evidence_grade: str
    observed_at: str
    valid_until: Optional[str]
    redaction_status: str
    created_at: str


@dataclass(frozen=True)
class SignalBatch:
    signals: tuple[EditorialSignal, ...]
    claims: tuple[Claim, ...]
    evidence: tuple[Evidence, ...]
    momcozy_presence_status: str
    rule_version: str
    dictionary_version: str
    taxonomy_version: str
    generated_at: str


@dataclass(frozen=True)
class _Entity:
    key: str
    aliases: tuple[str, ...]
    entity_class: str


def _normalized_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def _contains(text: str, term: str) -> bool:
    escaped = re.escape(_normalized_text(term).casefold()).replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.casefold()))


def _entities(dictionary: Mapping[str, object]) -> tuple[_Entity, ...]:
    momcozy = dictionary.get("momcozy")
    competitors = dictionary.get("competitors")
    if not isinstance(momcozy, Mapping) or not isinstance(competitors, Mapping):
        raise ValueError("competitor_dictionary_structure_invalid")

    aliases = set(str(item) for item in momcozy.get("self_keywords", ()))
    aliases.update(str(item) for item in momcozy.get("models", ()))
    product_aliases = momcozy.get("product_aliases", {})
    if isinstance(product_aliases, Mapping):
        aliases.update(str(item) for item in product_aliases.values())
    result = [
        _Entity(
            key=str(momcozy.get("brand_key", "momcozy")),
            aliases=tuple(sorted(aliases, key=lambda value: (-len(value), value.casefold()))),
            entity_class="momcozy",
        )
    ]

    pump_rows = competitors.get("pump")
    if not isinstance(pump_rows, Sequence):
        raise ValueError("pump_competitor_dictionary_missing")
    for row in pump_rows:
        if not isinstance(row, Mapping):
            raise ValueError("pump_competitor_row_invalid")
        row_aliases = {str(row.get("name", ""))}
        row_aliases.update(str(item) for item in row.get("models", ()))
        row_aliases.update(str(item) for item in row.get("pr_keywords", ()))
        row_aliases.discard("")
        result.append(
            _Entity(
                key=str(row["brand_key"]),
                aliases=tuple(
                    sorted(row_aliases, key=lambda value: (-len(value), value.casefold()))
                ),
                entity_class="competitor",
            )
        )
    return tuple(result)


def _matched_entities(text: str, entities: Sequence[_Entity]) -> tuple[_Entity, ...]:
    return tuple(
        entity
        for entity in entities
        if any(_contains(text, alias) for alias in entity.aliases)
    )


def _stance(text: str) -> str:
    folded = text.casefold()
    positive = any(marker in folded for marker in _POSITIVE_MARKERS)
    negative = any(marker in folded for marker in _NEGATIVE_MARKERS)
    if positive and negative:
        return "mixed"
    if positive:
        return "positive"
    if negative:
        return "negative"
    return "neutral"


def _topic(text: str) -> str:
    return (
        "pumping_product_review"
        if any(_contains(text, marker) for marker in _CATEGORY_MARKERS)
        else "unclassified"
    )


def _risk_type(text: str, dictionary: Mapping[str, object]) -> Optional[str]:
    folded = text.casefold()
    if any(marker in folded for marker in _QUALITY_MARKERS):
        return "quality"
    rows = dictionary.get("risk_keywords", ())
    if not isinstance(rows, Sequence):
        raise ValueError("risk_keyword_dictionary_invalid")
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        term = str(row.get("term", ""))
        if term and _contains(text, term):
            source_type = str(row.get("type", ""))
            if "隐私" in source_type:
                return "privacy"
            if "FTC" in source_type or "真实" in source_type:
                return "authenticity"
            if "法律" in source_type or "监管" in source_type:
                return "legal"
            if "安全" in source_type:
                return "product_safety"
            return "reputational"
    return None


def _make_signal(
    analysis_document: AnalysisDocument,
    *,
    signal_type: str,
    subject_entity: Optional[str],
    topic_key: str,
    stance: str,
    claim_text: str,
    confidence: float,
    versions: SignalVersions,
) -> tuple[EditorialSignal, Claim, tuple[Evidence, ...]]:
    document = analysis_document.document
    evidence_span = _normalized_text(analysis_document.allowed_evidence_text)[:500]
    signal_id = stable_id(
        "signal",
        document.document_id,
        signal_type,
        subject_entity or "none",
        topic_key,
        versions.rule_version,
        versions.dictionary_version,
        versions.taxonomy_version,
    )
    claim_id = stable_id("claim", signal_id, claim_text)
    evidence_set_id = stable_id("evidence_set", signal_id, claim_id)
    evidence: list[Evidence] = []
    supporting_id = stable_id(
        "evidence", claim_id, document.document_id, "supports", evidence_span
    )
    evidence.append(
        Evidence(
            evidence_id=supporting_id,
            claim_id=claim_id,
            document_id=document.document_id,
            quote_span=evidence_span,
            supports_or_refutes="supports",
            evidence_grade=analysis_document.evidence_grade,
            observed_at=document.fetched_at,
            valid_until=None,
            redaction_status="active",
            created_at=document.fetched_at,
        )
    )
    counter_ids: list[str] = []
    for counter in analysis_document.counterevidence:
        normalized = _normalized_text(counter.quote_span)[:500]
        if not normalized:
            continue
        evidence_id = stable_id(
            "evidence", claim_id, counter.document_id, "refutes", normalized
        )
        counter_ids.append(evidence_id)
        evidence.append(
            Evidence(
                evidence_id=evidence_id,
                claim_id=claim_id,
                document_id=counter.document_id,
                quote_span=normalized,
                supports_or_refutes="refutes",
                evidence_grade=counter.evidence_grade,
                observed_at=counter.observed_at,
                valid_until=None,
                redaction_status="active",
                created_at=counter.observed_at,
            )
        )

    verification_status = (
        "credible_single_source" if subject_entity is not None else "unverified"
    )
    claim = Claim(
        claim_id=claim_id,
        claim_text=claim_text,
        claimant_text=document.author_text or document.edition_id,
        subject=subject_entity or "unresolved_entity",
        predicate=signal_type,
        time_scope=document.published_at,
        verification_status=verification_status,
        evidence_ids=(supporting_id,),
        counterevidence_ids=tuple(counter_ids),
        confidence=confidence,
        markets=("US",),
        entities=(subject_entity,) if subject_entity else (),
        model_name=versions.model_name,
        model_version=versions.model_version or versions.rule_version,
        prompt_version=versions.prompt_version,
        review_status="pending_review",
        created_at=document.fetched_at,
    )
    signal = EditorialSignal(
        signal_id=signal_id,
        document_id=document.document_id,
        edition_id=document.edition_id,
        journalist_id=(
            document.journalist_id
            if str(document.byline_status.value) == "verified"
            else None
        ),
        signal_type=signal_type,
        subject_entity=subject_entity,
        topic_key=topic_key,
        stance=stance,
        claim_text=claim_text,
        evidence_span=evidence_span,
        sponsorship_status=document.sponsorship_status,
        confidence=confidence,
        review_status="pending_review",
        evidence_set_id=evidence_set_id,
        claim_id=claim_id,
        rule_version=versions.rule_version,
        model_name=versions.model_name,
        model_version=versions.model_version,
        prompt_version=versions.prompt_version,
        created_at=document.fetched_at,
    )
    return signal, claim, tuple(evidence)


def extract_signals(
    documents: Sequence[AnalysisDocument],
    dictionaries: Mapping[str, object],
    taxonomy: Mapping[str, object],
    versions: SignalVersions,
) -> SignalBatch:
    """Extract explainable candidates without treating a stance as verified truth."""
    if str(dictionaries.get("version")) != versions.dictionary_version:
        raise ValueError("competitor_dictionary_version_mismatch")
    if str(taxonomy.get("version")) != versions.taxonomy_version:
        raise ValueError("taxonomy_version_mismatch")
    allowed_signal_types = set(str(item) for item in taxonomy.get("signal_types", ()))
    allowed_stances = set(str(item) for item in taxonomy.get("stances", ()))
    entities = _entities(dictionaries)
    signals: list[EditorialSignal] = []
    claims: list[Claim] = []
    evidence: list[Evidence] = []
    momcozy_observed = False

    for analysis_document in documents:
        document = analysis_document.document
        text = _normalized_text(analysis_document.allowed_evidence_text)
        searchable = f"{document.title or ''} {text}"
        matched = _matched_entities(searchable, entities)
        topic_key = _topic(searchable)
        observed_stance = _stance(text)
        momcozy_entities = tuple(x for x in matched if x.entity_class == "momcozy")
        competitor_entities = tuple(x for x in matched if x.entity_class == "competitor")
        momcozy_observed = momcozy_observed or bool(momcozy_entities)

        candidates: list[tuple[str, Optional[str], str, str, float]] = []
        if document.sponsorship_status != "unknown":
            candidates.append(
                (
                    "content_disclosure",
                    None,
                    "neutral",
                    f"Content disclosure is {document.sponsorship_status}",
                    1.0,
                )
            )
        if topic_key != "unclassified":
            candidates.append(
                (
                    "recent_topic",
                    None,
                    "neutral",
                    f"Document discusses topic {topic_key}",
                    0.8,
                )
            )
        for entity in competitor_entities:
            candidates.append(
                (
                    "competitor_view",
                    entity.key,
                    observed_stance,
                    f"Document expresses a {observed_stance} view of {entity.key}",
                    0.78,
                )
            )
        for entity in momcozy_entities:
            candidates.append(
                (
                    "momcozy_mention",
                    entity.key,
                    observed_stance,
                    f"Document contains a {observed_stance} Momcozy mention",
                    0.82,
                )
            )
        risk_type = _risk_type(searchable, dictionaries)
        if risk_type is not None:
            risk_subject = (
                momcozy_entities[0].key
                if momcozy_entities
                else competitor_entities[0].key
                if competitor_entities
                else None
            )
            candidates.append(
                (
                    "media_risk",
                    risk_subject,
                    "negative",
                    f"Document contains a {risk_type} risk candidate",
                    0.85 if risk_subject else 0.35,
                )
            )

        for signal_type, subject, stance, claim_text, confidence in candidates:
            if signal_type not in allowed_signal_types:
                raise ValueError(f"signal_type_not_in_taxonomy:{signal_type}")
            if stance not in allowed_stances:
                raise ValueError(f"stance_not_in_taxonomy:{stance}")
            signal, claim, signal_evidence = _make_signal(
                analysis_document,
                signal_type=signal_type,
                subject_entity=subject,
                topic_key=topic_key,
                stance=stance,
                claim_text=claim_text,
                confidence=confidence,
                versions=versions,
            )
            signals.append(signal)
            claims.append(claim)
            evidence.extend(signal_evidence)

    signals.sort(key=lambda item: item.signal_id)
    claims.sort(key=lambda item: item.claim_id)
    evidence.sort(key=lambda item: item.evidence_id)
    if not documents:
        presence = "unknown"
        generated_at = "1970-01-01T00:00:00Z"
    else:
        presence = "observed" if momcozy_observed else "not_observed_in_covered_data"
        generated_at = max(item.document.fetched_at for item in documents)
    if presence not in _PRESENCE_STATUSES:
        raise AssertionError("presence_status_contract_broken")
    return SignalBatch(
        signals=tuple(signals),
        claims=tuple(claims),
        evidence=tuple(evidence),
        momcozy_presence_status=presence,
        rule_version=versions.rule_version,
        dictionary_version=versions.dictionary_version,
        taxonomy_version=versions.taxonomy_version,
        generated_at=generated_at,
    )
