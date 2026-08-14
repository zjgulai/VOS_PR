from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timezone

from tools.pr_intel.core_media.action_service import (
    ActionProposal,
    InvalidTransition,
    create_action_draft,
    transition_action,
)
from tools.pr_intel.core_media.brief_generator import (
    BriefContext,
    BriefVersions,
    generate_media_brief,
)
from tools.pr_intel.core_media.contracts import CoverageStatus
from tools.pr_intel.core_media.coverage import CoverageReport
from tools.pr_intel.core_media.media_risk import MediaRiskCandidate
from tools.pr_intel.core_media.opportunity import Opportunity
from tools.pr_intel.core_media.relationship_rules import PitchReadinessDecision
from tools.pr_intel.core_media.signal_extractor import EditorialSignal, Evidence


NOW = datetime(2026, 8, 14, 12, tzinfo=timezone.utc)


def _signal() -> EditorialSignal:
    return EditorialSignal(
        signal_id="signal_fixture",
        document_id="document_fixture",
        edition_id="edition_fixture",
        journalist_id=None,
        signal_type="competitor_view",
        subject_entity="eufy",
        topic_key="pumping_product_review",
        stance="mixed",
        claim_text="Document expresses a mixed view of eufy",
        evidence_span="Eufy is quiet but suction is weak.",
        sponsorship_status="editorial",
        confidence=0.78,
        review_status="pending_review",
        evidence_set_id="evidence_set_signal",
        claim_id="claim_fixture",
        rule_version="signal-v1",
        model_name=None,
        model_version=None,
        prompt_version=None,
        created_at="2026-08-14T00:00:00Z",
    )


def _evidence() -> Evidence:
    return Evidence(
        evidence_id="evidence_fixture",
        claim_id="claim_fixture",
        document_id="document_fixture",
        quote_span="Eufy is quiet but suction is weak.",
        supports_or_refutes="supports",
        evidence_grade="synthetic_gold",
        observed_at="2026-08-14T00:00:00Z",
        valid_until=None,
        redaction_status="active",
        created_at="2026-08-14T00:00:00Z",
    )


def _coverage(*, actual: bool = True) -> CoverageReport:
    return CoverageReport(
        requested_start="2026-07-15T00:00:00Z",
        requested_end="2026-08-14T00:00:00Z",
        actual_start="2026-07-20T00:00:00Z" if actual else None,
        actual_end="2026-08-14T00:00:00Z" if actual else None,
        documents_seen=3,
        documents_accepted=2,
        status=CoverageStatus.PARTIAL,
        entries=(),
        generated_at="2026-08-14T00:00:00Z",
    )


def _opportunity() -> Opportunity:
    return Opportunity(
        opportunity_id="opportunity_fixture",
        edition_id="edition_fixture",
        journalist_id=None,
        topic_fit=0.9,
        timing=0.8,
        competitor_gap=0.8,
        momcozy_presence="not_observed_in_covered_data",
        evidence_strength=0.9,
        asset_gap=("independent_lab_data",),
        relationship_penalty=0.0,
        risk_penalty=0.0,
        rank_group="priority_candidate",
        angle="Independent comfort evidence",
        why_now="Recent covered competitor comparison",
        evidence_set_id="evidence_set_signal",
        review_status="pending_review",
        created_at="2026-08-14T00:00:00Z",
        updated_at="2026-08-14T00:00:00Z",
    )


def _risk() -> MediaRiskCandidate:
    return MediaRiskCandidate(
        media_risk_id="risk_fixture",
        document_id="document_fixture",
        edition_id="edition_fixture",
        journalist_id=None,
        risk_type="quality",
        brand_relevance="direct",
        product_relevance="direct",
        category_relevance="direct",
        evidence_span="Fixture evidence",
        sponsorship_status="editorial",
        priority="high",
        review_status="pending_review",
        escalation_result="awaiting_human_review",
        evidence_set_id="evidence_set_signal",
        created_at="2026-08-14T00:00:00Z",
        updated_at="2026-08-14T00:00:00Z",
    )


def _brief_context(
    *,
    requested_scope_type: str = "edition",
    identity_verified: bool = False,
    evidence_sufficient: bool = True,
    actual_coverage: bool = True,
    pitch_status: str = "review_required",
) -> BriefContext:
    return BriefContext(
        requested_scope_type=requested_scope_type,
        requested_scope_id=(
            "journalist_fixture"
            if requested_scope_type == "journalist"
            else "edition_fixture"
        ),
        edition_id="edition_fixture",
        journalist_id=(
            "journalist_fixture" if requested_scope_type == "journalist" else None
        ),
        identity_verified=identity_verified,
        evidence_sufficient=evidence_sufficient,
        window_start=datetime(2026, 7, 15, tzinfo=timezone.utc),
        window_end=NOW,
        baseline_start=datetime(2026, 2, 15, tzinfo=timezone.utc),
        baseline_end=NOW,
        coverage=_coverage(actual=actual_coverage),
        signals=(_signal(),),
        evidence=(_evidence(),),
        opportunities=(_opportunity(),),
        media_risks=(_risk(),),
        pitch_readiness=PitchReadinessDecision(
            decision_id="pitch_decision_fixture",
            status=pitch_status,
            reason_codes=("asset_gap",) if pitch_status != "ready" else (),
            constraint_ids=("constraint_fixture",) if pitch_status != "ready" else (),
        ),
        momcozy_presence_status="not_observed_in_covered_data",
        explicit_uncertainties=("source coverage is partial",),
        registry_version="registry-fixture-v1",
        generated_at=NOW,
        versions=BriefVersions(
            rule_version="brief-rules-v1",
            model_name=None,
            model_version=None,
            prompt_version=None,
        ),
    )


class BriefTests(unittest.TestCase):
    def test_brief_is_complete_evidence_bound_and_deterministic(self) -> None:
        first = generate_media_brief(_brief_context())
        second = generate_media_brief(_brief_context())
        self.assertEqual(first, second)
        self.assertEqual("edition", first.scope_type)
        self.assertEqual("2026-07-20T00:00:00Z", first.actual_coverage_start)
        self.assertEqual(2, first.document_count)
        self.assertTrue(first.recent_focus)
        self.assertEqual(("signal_fixture",), first.competitor_view_ids)
        self.assertEqual("not_observed_in_covered_data", first.momcozy_presence_status)
        self.assertEqual(("opportunity_fixture",), first.opportunity_ids)
        self.assertEqual(("risk_fixture",), first.media_risk_ids)
        self.assertEqual(("constraint_fixture",), first.pitch_constraint_ids)
        self.assertTrue(first.uncertainties)
        self.assertEqual(("evidence_fixture",), first.evidence_ids)
        self.assertEqual(("evidence_fixture",), first.fact_items[0].evidence_ids)
        self.assertTrue(all(item.label == "analysis" for item in first.inference_items))

    def test_unverified_or_evidence_insufficient_journalist_brief_downgrades(self) -> None:
        for identity_verified, evidence_sufficient in ((False, True), (True, False)):
            with self.subTest(
                identity_verified=identity_verified,
                evidence_sufficient=evidence_sufficient,
            ):
                brief = generate_media_brief(
                    _brief_context(
                        requested_scope_type="journalist",
                        identity_verified=identity_verified,
                        evidence_sufficient=evidence_sufficient,
                    )
                )
                self.assertEqual("edition", brief.scope_type)
                self.assertEqual("edition_fixture", brief.scope_id)
                self.assertIn("journalist_scope_downgraded", brief.uncertainties)

    def test_not_observed_requires_an_actual_coverage_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "momcozy_gap_requires_actual_coverage"):
            generate_media_brief(_brief_context(actual_coverage=False))


class ActionStateMachineTests(unittest.TestCase):
    def _proposal(self) -> ActionProposal:
        return ActionProposal(
            action_type="media_pitch",
            title="Fixture pitch",
            why_now="Recent covered competitor comparison",
            target_outlet_text="Fixture Outlet",
            target_journalist_text=None,
            content_angle="Independent comfort evidence",
            required_assets=("independent_lab_data",),
            owner_role="media_relations_lead",
            due_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
            success_metric="PR lead records a decision",
            risk_text="No preview demand and no unsupported product claim",
            source_insight_ids=("signal_fixture",),
        )

    def test_action_inherits_brief_evidence_constraints_and_starts_pending(self) -> None:
        action = create_action_draft(
            generate_media_brief(_brief_context()), self._proposal()
        )
        self.assertEqual("edition_fixture", action.edition_id)
        self.assertIsNone(action.journalist_id)
        self.assertEqual(("constraint_fixture",), action.pitch_constraint_ids)
        self.assertTrue(action.evidence_set_id)
        self.assertEqual("pending", action.approval_status)
        self.assertEqual("not_started", action.execution_status)
        self.assertFalse(hasattr(action, "send"))

    def test_pending_action_cannot_start_execution(self) -> None:
        action = create_action_draft(
            generate_media_brief(_brief_context()), self._proposal()
        )
        with self.assertRaisesRegex(InvalidTransition, "approval_required"):
            transition_action(
                action,
                "start",
                "media_relations_lead",
                occurred_at=NOW,
            )

    def test_approved_action_can_start_and_finish_with_result(self) -> None:
        action = create_action_draft(
            generate_media_brief(_brief_context(pitch_status="ready")),
            self._proposal(),
        )
        approved = transition_action(
            action,
            "approve",
            "pr_lead",
            note="Evidence and wording reviewed",
            occurred_at=NOW,
        )
        started = transition_action(
            approved,
            "start",
            "media_relations_lead",
            occurred_at=NOW,
        )
        done = transition_action(
            started,
            "complete",
            "media_relations_lead",
            note="Decision recorded in fixture",
            occurred_at=NOW,
        )
        self.assertEqual("approved", done.approval_status)
        self.assertEqual("done", done.execution_status)
        self.assertEqual("Decision recorded in fixture", done.result_note)
        self.assertEqual(3, len(done.transition_history))

    def test_rejected_or_blocked_action_cannot_be_executed(self) -> None:
        action = create_action_draft(
            generate_media_brief(_brief_context()), self._proposal()
        )
        rejected = transition_action(
            action,
            "reject",
            "pr_lead",
            note="Not aligned",
            occurred_at=NOW,
        )
        with self.assertRaisesRegex(InvalidTransition, "approval_state_terminal"):
            transition_action(
                rejected,
                "approve",
                "pr_lead",
                occurred_at=NOW,
            )

    def test_blocked_pitch_readiness_creates_blocked_action(self) -> None:
        brief = generate_media_brief(_brief_context(pitch_status="blocked"))
        action = create_action_draft(brief, self._proposal())
        self.assertEqual("blocked", action.approval_status)
        with self.assertRaisesRegex(InvalidTransition, "approval_required"):
            transition_action(
                action,
                "start",
                "media_relations_lead",
                occurred_at=NOW,
            )

    def test_action_transition_roles_and_result_note_are_enforced(self) -> None:
        action = create_action_draft(
            generate_media_brief(_brief_context(pitch_status="ready")),
            self._proposal(),
        )
        with self.assertRaisesRegex(InvalidTransition, "review_role_required"):
            transition_action(action, "approve", "viewer", occurred_at=NOW)
        approved = transition_action(action, "approve", "pr_lead", occurred_at=NOW)
        started = transition_action(
            approved, "start", "media_relations_lead", occurred_at=NOW
        )
        with self.assertRaisesRegex(InvalidTransition, "result_note_required"):
            transition_action(
                started,
                "complete",
                "media_relations_lead",
                occurred_at=NOW,
            )


if __name__ == "__main__":
    unittest.main()
