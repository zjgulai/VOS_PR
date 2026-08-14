from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools.pr_intel.core_media.contracts import BylineStatus
from tools.pr_intel.core_media.media_risk import evaluate_media_risk
from tools.pr_intel.core_media.normalizer import Document
from tools.pr_intel.core_media.opportunity import OpportunityContext, rank_opportunities
from tools.pr_intel.core_media.signal_extractor import (
    AnalysisDocument,
    CounterEvidenceInput,
    SignalVersions,
    extract_signals,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pr_core_media/uat_expected.json"
DICTIONARY = ROOT / "config/competitor_dictionary.json"
TAXONOMY = ROOT / "config/pr_core_media_taxonomy.json"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text("utf-8"))


def _case(case_id: str) -> dict[str, object]:
    rows = _load_json(FIXTURE)["signal_cases"]
    return next(row for row in rows if row["case_id"] == case_id)


def _analysis_document(case_id: str) -> AnalysisDocument:
    row = _case(case_id)
    now = "2026-08-14T00:00:00Z"
    document = Document(
        version="1.1",
        document_id=f"document_{case_id}",
        source_id="source_fixture",
        edition_id="edition_fixture_us_en",
        canonical_url=str(row["url"]),
        published_at="2026-08-13T12:00:00Z",
        fetched_at=now,
        title=str(row["title"]),
        author_text="Fixture Author",
        journalist_id=None,
        byline_status=BylineStatus.UNVERIFIED,
        content_type=str(row["content_type"]),
        sponsorship_status=str(row["sponsorship_status"]),
        text_hash=f"hash_{case_id}",
        rights_label="excerpt_only",
        is_syndicated=row["sponsorship_status"] == "syndicated",
        canonical_document_id=(
            "document_original_fixture"
            if row["sponsorship_status"] == "syndicated"
            else None
        ),
        deletion_status="active",
        raw_object_ref=f"fixture://{case_id}",
        quality_issues=(),
        trend_eligible=True,
        created_at=now,
        updated_at=now,
    )
    return AnalysisDocument(
        document=document,
        allowed_evidence_text=str(row["text"]),
        counterevidence=tuple(
            CounterEvidenceInput(
                document_id=str(item["document_id"]),
                quote_span=str(item["quote_span"]),
                observed_at=str(item["observed_at"]),
                evidence_grade=str(item["evidence_grade"]),
            )
            for item in row.get("counterevidence", ())
        ),
        evidence_grade="synthetic_gold",
    )


def _versions() -> SignalVersions:
    return SignalVersions(
        rule_version="signal_rules_fixture_v1",
        dictionary_version="1.0",
        taxonomy_version="1.0-draft",
    )


class SignalGoldSetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dictionary = _load_json(DICTIONARY)
        cls.taxonomy = _load_json(TAXONOMY)

    def test_gold_set_covers_required_disclosures_stances_presence_and_risk(self) -> None:
        fixture = _load_json(FIXTURE)
        cases = fixture["signal_cases"]
        self.assertTrue(fixture["synthetic_only"])
        self.assertEqual(
            {"editorial", "sponsored", "affiliate", "syndicated"},
            {row["sponsorship_status"] for row in cases},
        )
        self.assertEqual(
            {"positive", "negative", "mixed"},
            {row["expected_stance"] for row in cases if "expected_stance" in row},
        )
        self.assertEqual(
            {"observed", "not_observed_in_covered_data"},
            {row["expected_presence"] for row in cases if "expected_presence" in row},
        )
        self.assertTrue(any(row.get("counterevidence") for row in cases))
        self.assertEqual(15, len(fixture["acceptance_scenarios"]))

    def test_competitor_view_keeps_stance_separate_from_truth(self) -> None:
        batch = extract_signals(
            (_analysis_document("competitor_mixed_affiliate"),),
            self.dictionary,
            self.taxonomy,
            _versions(),
        )
        signal = next(item for item in batch.signals if item.signal_type == "competitor_view")
        claim = next(item for item in batch.claims if item.claim_id == signal.claim_id)
        self.assertEqual("eufy", signal.subject_entity)
        self.assertEqual("mixed", signal.stance)
        self.assertEqual("credible_single_source", claim.verification_status)
        self.assertTrue(claim.counterevidence_ids)
        self.assertEqual("affiliate", signal.sponsorship_status)

    def test_presence_is_bounded_to_observed_documents(self) -> None:
        observed = extract_signals(
            (_analysis_document("momcozy_observed_quality"),),
            self.dictionary,
            self.taxonomy,
            _versions(),
        )
        gap = extract_signals(
            (_analysis_document("momcozy_not_observed"),),
            self.dictionary,
            self.taxonomy,
            _versions(),
        )
        unknown = extract_signals((), self.dictionary, self.taxonomy, _versions())
        self.assertEqual("observed", observed.momcozy_presence_status)
        self.assertEqual("not_observed_in_covered_data", gap.momcozy_presence_status)
        self.assertEqual("unknown", unknown.momcozy_presence_status)

    def test_same_input_and_versions_produce_stable_signal_and_evidence_ids(self) -> None:
        inputs = (_analysis_document("competitor_positive_editorial"),)
        first = extract_signals(inputs, self.dictionary, self.taxonomy, _versions())
        second = extract_signals(inputs, self.dictionary, self.taxonomy, _versions())
        self.assertEqual(first, second)
        self.assertTrue(first.signals[0].evidence_set_id)
        self.assertTrue(first.evidence)


class MediaRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dictionary = _load_json(DICTIONARY)
        cls.taxonomy = _load_json(TAXONOMY)

    def _risk(self, case_id: str):
        analysis_document = _analysis_document(case_id)
        batch = extract_signals(
            (analysis_document,), self.dictionary, self.taxonomy, _versions()
        )
        signal = next(item for item in batch.signals if item.signal_type == "media_risk")
        return evaluate_media_risk(signal, analysis_document.document)

    def test_generic_risk_word_without_entity_relevance_is_rejected(self) -> None:
        candidate = self._risk("unrelated_recall_false_positive")
        self.assertEqual("rejected_by_relevance_gate", candidate.review_status)
        self.assertEqual("none", candidate.priority)
        self.assertEqual("not_relevant", candidate.brand_relevance)
        self.assertEqual("not_relevant", candidate.product_relevance)
        self.assertEqual("not_relevant", candidate.category_relevance)

    def test_direct_momcozy_quality_evidence_requires_human_review(self) -> None:
        candidate = self._risk("momcozy_observed_quality")
        self.assertEqual("pending_review", candidate.review_status)
        self.assertEqual("high", candidate.priority)
        self.assertEqual("direct", candidate.brand_relevance)
        self.assertEqual("awaiting_human_review", candidate.escalation_result)
        self.assertTrue(candidate.evidence_set_id)


class OpportunityTests(unittest.TestCase):
    def test_opportunities_preserve_factors_without_pseudo_precise_score(self) -> None:
        now = datetime(2026, 8, 14, tzinfo=timezone.utc)
        ranked = rank_opportunities(
            (
                OpportunityContext(
                    edition_id="edition_high",
                    journalist_id=None,
                    topic_fit=0.9,
                    timing=0.8,
                    competitor_gap=0.9,
                    momcozy_presence="not_observed_in_covered_data",
                    evidence_strength=0.9,
                    asset_gap=("lab_test",),
                    relationship_penalty=0.0,
                    risk_penalty=0.0,
                    angle="Independent comfort and suction evidence",
                    why_now="Recent competitor comparison with a covered-data Momcozy gap",
                    evidence_set_id="evidence_set_high",
                ),
                OpportunityContext(
                    edition_id="edition_blocked",
                    journalist_id="journalist_fixture",
                    topic_fit=1.0,
                    timing=1.0,
                    competitor_gap=1.0,
                    momcozy_presence="not_observed_in_covered_data",
                    evidence_strength=1.0,
                    asset_gap=(),
                    relationship_penalty=1.0,
                    risk_penalty=0.0,
                    angle="Blocked fixture",
                    why_now="Recent signal",
                    evidence_set_id="evidence_set_blocked",
                ),
            ),
            generated_at=now,
        )
        self.assertEqual(["priority_candidate", "blocked"], [x.rank_group for x in ranked])
        self.assertFalse(hasattr(ranked[0], "score"))
        self.assertEqual("not_observed_in_covered_data", ranked[0].momcozy_presence)
        self.assertEqual(("lab_test",), ranked[0].asset_gap)
        self.assertEqual("pending_review", ranked[0].review_status)


if __name__ == "__main__":
    unittest.main()
