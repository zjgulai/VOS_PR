from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from tools.pr_intel.core_media.relationship_rules import (
    DocumentTopic,
    PitchReadinessContext,
    RelationshipEvent,
    RelationshipRules,
    calculate_backfill_metric,
    derive_pitch_constraints,
    evaluate_pitch_readiness,
    override_pitch_constraint,
)


UTC = timezone.utc
AS_OF = datetime(2026, 8, 14, 12, tzinfo=UTC)


def _event(
    event_type: str,
    *,
    days_ago: int | None,
    outcome: str | None = None,
    review_status: str = "verified",
    created_delay_days: int = 1,
) -> RelationshipEvent:
    occurred_at = None if days_ago is None else AS_OF - timedelta(days=days_ago)
    created_at = (
        None
        if occurred_at is None
        else occurred_at + timedelta(days=created_delay_days)
    )
    return RelationshipEvent(
        event_id=f"event_{event_type}_{days_ago}",
        journalist_id="journalist_fixture",
        edition_id="edition_fixture",
        event_type=event_type,
        occurred_at=occurred_at,
        outcome=outcome,
        owner_role="media_relations",
        source_type="synthetic_fixture",
        source_row_ref="fixture!1",
        review_status=review_status,
        created_at=created_at,
    )


def _rules(*, approved: bool = True) -> RelationshipRules:
    return RelationshipRules(
        rule_version="relationship_fixture_v1",
        recent_contact_days=30,
        same_topic_cooldown_days=30,
        approval_status="approved" if approved else "pending_business_signoff",
        decision_ref="fixture:gate0" if approved else None,
        override_roles=("pr_lead", "admin"),
    )


class ConstraintDerivationTests(unittest.TestCase):
    def test_undated_history_note_does_not_create_automatic_cooldown(self) -> None:
        constraints = derive_pitch_constraints(
            (_event("relationship_note", days_ago=None),), (), AS_OF, _rules()
        )
        self.assertEqual((), constraints)

    def test_recent_pitch_blocks_action_with_auditable_reason(self) -> None:
        constraints = derive_pitch_constraints(
            (_event("pitch_sent", days_ago=12),), (), AS_OF, _rules()
        )
        decision = evaluate_pitch_readiness(
            PitchReadinessContext(
                edition_id="edition_fixture",
                journalist_id="journalist_fixture",
                target_topic_key="pumping_product_review",
                constraints=constraints,
                evidence_sufficient=True,
                coverage_sufficient=True,
                identity_verified=True,
                asset_gap=(),
                unresolved_media_risk=False,
            )
        )
        self.assertEqual("blocked", decision.status)
        self.assertIn("recent_contact_30d", decision.reason_codes)
        self.assertEqual(("event_pitch_sent_12",), constraints[0].evidence_refs)
        self.assertEqual("active", constraints[0].status)

    def test_recent_same_topic_document_creates_topic_specific_cooldown(self) -> None:
        documents = (
            DocumentTopic(
                document_id="document_recent_topic",
                edition_id="edition_fixture",
                journalist_id="journalist_fixture",
                topic_key="pumping_product_review",
                published_at=AS_OF - timedelta(days=8),
            ),
        )
        constraints = derive_pitch_constraints((), documents, AS_OF, _rules())
        decision = evaluate_pitch_readiness(
            PitchReadinessContext(
                edition_id="edition_fixture",
                journalist_id="journalist_fixture",
                target_topic_key="pumping_product_review",
                constraints=constraints,
                evidence_sufficient=True,
                coverage_sufficient=True,
                identity_verified=True,
                asset_gap=(),
                unresolved_media_risk=False,
            )
        )
        self.assertEqual("cooldown", decision.status)
        self.assertEqual(("same_topic_cooldown",), decision.reason_codes)

    def test_unsigned_gate0_rules_cannot_make_a_ready_or_blocked_decision(self) -> None:
        constraints = derive_pitch_constraints(
            (_event("pitch_sent", days_ago=4),), (), AS_OF, _rules(approved=False)
        )
        self.assertEqual("pending_rule_approval", constraints[0].status)
        decision = evaluate_pitch_readiness(
            PitchReadinessContext(
                edition_id="edition_fixture",
                journalist_id="journalist_fixture",
                target_topic_key="pumping_product_review",
                constraints=constraints,
                evidence_sufficient=True,
                coverage_sufficient=True,
                identity_verified=True,
                asset_gap=(),
                unresolved_media_risk=False,
            )
        )
        self.assertEqual("review_required", decision.status)
        self.assertIn("pending_rule_approval", decision.reason_codes)

    def test_override_requires_authorized_role_and_preserves_approval_evidence(self) -> None:
        constraint = derive_pitch_constraints(
            (_event("do_not_contact", days_ago=50),), (), AS_OF, _rules()
        )[0]
        with self.assertRaisesRegex(ValueError, "constraint_override_role_forbidden"):
            override_pitch_constraint(
                constraint,
                approved_by_role="analyst",
                approved_at=AS_OF,
                evidence_ref="decision:fixture",
                rules=_rules(),
            )
        overridden = override_pitch_constraint(
            constraint,
            approved_by_role="pr_lead",
            approved_at=AS_OF,
            evidence_ref="decision:fixture",
            rules=_rules(),
        )
        self.assertEqual("overridden", overridden.status)
        self.assertEqual("pr_lead", overridden.approved_by_role)
        self.assertEqual("decision:fixture", overridden.override_evidence_ref)
        self.assertEqual(AS_OF, overridden.approved_at)


class ReadinessAndMetricTests(unittest.TestCase):
    def test_missing_evidence_asset_and_identity_are_review_required(self) -> None:
        decision = evaluate_pitch_readiness(
            PitchReadinessContext(
                edition_id="edition_fixture",
                journalist_id="journalist_fixture",
                target_topic_key="pumping_product_review",
                constraints=(),
                evidence_sufficient=False,
                coverage_sufficient=False,
                identity_verified=False,
                asset_gap=("independent_lab_data",),
                unresolved_media_risk=True,
            )
        )
        self.assertEqual("review_required", decision.status)
        self.assertEqual(
            (
                "insufficient_evidence",
                "coverage_gap",
                "unverified_identity",
                "asset_gap",
                "unresolved_media_risk",
            ),
            decision.reason_codes,
        )

    def test_ready_requires_no_constraints_and_complete_gates(self) -> None:
        decision = evaluate_pitch_readiness(
            PitchReadinessContext(
                edition_id="edition_fixture",
                journalist_id=None,
                target_topic_key="pumping_product_review",
                constraints=(),
                evidence_sufficient=True,
                coverage_sufficient=True,
                identity_verified=False,
                asset_gap=(),
                unresolved_media_risk=False,
            )
        )
        self.assertEqual("ready", decision.status)
        self.assertEqual((), decision.reason_codes)

    def test_three_business_day_metric_excludes_missing_and_flags_invalid_times(self) -> None:
        friday = datetime(2026, 8, 7, 10, tzinfo=UTC)
        events = (
            RelationshipEvent(
                event_id="timely_weekend",
                journalist_id=None,
                edition_id="edition_fixture",
                event_type="pitch_sent",
                occurred_at=friday,
                outcome=None,
                owner_role="media_relations",
                source_type="fixture",
                source_row_ref=None,
                review_status="verified",
                created_at=datetime(2026, 8, 12, 10, tzinfo=UTC),
            ),
            _event("reply_received", days_ago=None),
            _event("sample_sent", days_ago=3, created_delay_days=-1),
        )
        metric = calculate_backfill_metric(events)
        self.assertEqual(1, metric.eligible_events)
        self.assertEqual(1, metric.timely_events)
        self.assertEqual(1.0, metric.timely_rate)
        self.assertEqual(("event_reply_received_None",), metric.missing_timestamp_event_ids)
        self.assertEqual(("event_sample_sent_3",), metric.invalid_order_event_ids)


if __name__ == "__main__":
    unittest.main()
