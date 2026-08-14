from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from tools.pr_intel.core_media.byline_resolver import (
    JournalistAffiliation,
    resolve_byline,
)
from tools.pr_intel.core_media.connectors.base import (
    CollectedRecord,
    CollectionResult,
    load_capabilities,
)
from tools.pr_intel.core_media.contracts import (
    BylineStatus,
    CoverageStatus,
    PermissionStatus,
    RightsLabel,
)
from tools.pr_intel.core_media.coverage import CoverageJob, build_coverage_report
from tools.pr_intel.core_media.normalizer import normalize_records
from tools.pr_intel.core_media.raw_archive import RawEnvelope, archive_envelope


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/pr_core_media/documents_synthetic.json"
CAPABILITY_PATH = ROOT / "tests/fixtures/pr_core_media/source_capabilities_synthetic.json"


def fixture_data() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def approved_capability():
    base = load_capabilities(CAPABILITY_PATH)[0]
    return replace(
        base,
        permission_status=PermissionStatus.APPROVED,
        rights_label=RightsLabel.EXCERPT_ONLY,
        allowed_fields=(
            "title",
            "canonical_url",
            "author_text",
            "published_at",
            "summary_excerpt",
        ),
        retention_days=30,
        tracking_query_keys=("utm_source", "utm_medium", "utm_campaign"),
    )


class RawArchiveTests(unittest.TestCase):
    def test_metadata_only_archive_does_not_store_excerpt_or_full_text(self) -> None:
        payload = fixture_data()["metadata_envelope"]
        envelope = RawEnvelope(
            run_id="fixture-run",
            source_id="fixture-source",
            fetched_at=datetime(2026, 8, 14, tzinfo=timezone.utc),
            rights_label=RightsLabel.METADATA_ONLY,
            allowed_fields=(
                "title",
                "canonical_url",
                "author_text",
                "published_at",
                "summary_excerpt",
                "full_text",
            ),
            retention_days=30,
            records=tuple(payload["records"]),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            first = archive_envelope(envelope, Path(temp_dir))
            second = archive_envelope(envelope, Path(temp_dir))
            serialized = Path(first.raw_object_ref).read_text(encoding="utf-8")

            self.assertNotIn("full_body_fixture_marker", serialized)
            self.assertNotIn("excerpt_fixture_marker", serialized)
            self.assertIn("Metadata-only article", serialized)
            self.assertEqual(first, second)
            self.assertEqual(1, len(list(Path(temp_dir).rglob("*.json"))))

    def test_archive_requires_retention_decision(self) -> None:
        envelope = RawEnvelope(
            run_id="fixture-run",
            source_id="fixture-source",
            fetched_at=datetime(2026, 8, 14, tzinfo=timezone.utc),
            rights_label=RightsLabel.METADATA_ONLY,
            allowed_fields=("title",),
            retention_days=None,
            records=({"title": "Fixture"},),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "retention_days_required"):
                archive_envelope(envelope, Path(temp_dir))


class NormalizationTests(unittest.TestCase):
    def _result(self) -> CollectionResult:
        records = tuple(
            CollectedRecord(
                canonical_url=item["canonical_url"],
                title=item["title"],
                author_text=item["author_text"],
                published_at=item["published_at"],
                summary_excerpt=item["summary_excerpt"],
                source_ref=f"fixture:{index}",
                sponsorship_disclosure=item["sponsorship_disclosure"],
                is_syndicated=item["is_syndicated"],
                canonical_document_id=item["canonical_document_id"],
            )
            for index, item in enumerate(fixture_data()["normalization_records"])
        )
        capability = approved_capability()
        return CollectionResult(
            source_id=capability.source_id,
            edition_id=capability.edition_id,
            coverage_status=CoverageStatus.COMPLETE,
            records=records,
            review_items=(),
            items_seen=len(records),
            items_accepted=len(records),
            error_code=None,
            safe_error_message=None,
            retry_after_seconds=None,
            fetched_at="2026-08-14T12:00:00Z",
            raw_object_ref="/tmp/fixture-envelope.json",
        )

    def test_url_timestamp_fingerprint_and_content_rules_are_deterministic(self) -> None:
        documents = normalize_records(self._result(), approved_capability())

        first = documents[0]
        self.assertEqual(
            "https://example.test/articles/review?variant=blue",
            first.canonical_url,
        )
        self.assertEqual("2026-08-12T10:00:00Z", first.published_at)
        self.assertEqual("review", first.content_type)
        self.assertEqual("unknown", first.sponsorship_status)
        self.assertTrue(first.trend_eligible)
        self.assertEqual(first, normalize_records(self._result(), approved_capability())[0])

        invalid = documents[1]
        self.assertIsNone(invalid.published_at)
        self.assertIn("invalid_timestamp", invalid.quality_issues)
        self.assertFalse(invalid.trend_eligible)
        self.assertEqual("affiliate", invalid.sponsorship_status)

        syndicated = documents[2]
        self.assertEqual("syndicated", syndicated.sponsorship_status)
        self.assertIn("syndication_canonical_missing", syndicated.quality_issues)
        self.assertFalse(syndicated.trend_eligible)

    def test_semantic_query_is_preserved_when_tracking_keys_are_not_signed(self) -> None:
        capability = replace(approved_capability(), tracking_query_keys=())

        document = normalize_records(self._result(), capability)[0]

        self.assertIn("utm_source=fixture", document.canonical_url)
        self.assertIn("variant=blue", document.canonical_url)


class CoverageReportTests(unittest.TestCase):
    def test_all_failure_and_success_states_remain_mutually_visible(self) -> None:
        start = datetime(2026, 8, 1, tzinfo=timezone.utc)
        end = datetime(2026, 8, 14, tzinfo=timezone.utc)
        statuses = (
            CoverageStatus.NO_MATCH,
            CoverageStatus.SOURCE_UNAVAILABLE,
            CoverageStatus.RATE_LIMITED,
            CoverageStatus.SCHEMA_CHANGED,
            CoverageStatus.PROFILE_INVALID,
            CoverageStatus.PERMISSION_PENDING,
            CoverageStatus.PARTIAL,
            CoverageStatus.COMPLETE,
        )
        jobs = []
        for index, status in enumerate(statuses):
            result = CollectionResult(
                source_id=f"source_{index}",
                edition_id="edition_fixture",
                coverage_status=status,
                records=(),
                review_items=(),
                items_seen=2 if status in {CoverageStatus.PARTIAL, CoverageStatus.COMPLETE} else 0,
                items_accepted=1 if status == CoverageStatus.PARTIAL else 2 if status == CoverageStatus.COMPLETE else 0,
                error_code=(None if status in {CoverageStatus.NO_MATCH, CoverageStatus.PARTIAL, CoverageStatus.COMPLETE} else status.value),
                safe_error_message=None,
                retry_after_seconds=17 if status == CoverageStatus.RATE_LIMITED else None,
                fetched_at="2026-08-14T12:00:00Z",
            )
            jobs.append(
                CoverageJob(
                    request_id=f"request_{index}",
                    requested_start=start,
                    requested_end=end,
                    actual_start=(start if status in {CoverageStatus.NO_MATCH, CoverageStatus.PARTIAL, CoverageStatus.COMPLETE} else None),
                    actual_end=(end if status in {CoverageStatus.NO_MATCH, CoverageStatus.PARTIAL, CoverageStatus.COMPLETE} else None),
                    result=result,
                    last_success_at=("2026-08-13T12:00:00Z" if status != CoverageStatus.PERMISSION_PENDING else None),
                )
            )

        report = build_coverage_report(tuple(jobs), (start, end))

        self.assertEqual(set(statuses), {entry.status for entry in report.entries})
        self.assertEqual(CoverageStatus.PARTIAL, report.status)
        self.assertEqual(4, report.documents_seen)
        self.assertEqual(3, report.documents_accepted)
        self.assertTrue(all("该媒体没有报道" not in entry.display_message for entry in report.entries))
        no_match = next(entry for entry in report.entries if entry.status == CoverageStatus.NO_MATCH)
        self.assertIn("不等同", no_match.display_message)


class BylineResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = normalize_records(
            NormalizationTests()._result(), approved_capability()
        )[0]
        self.verified = JournalistAffiliation(
            journalist_id="journalist_verified",
            edition_id=self.document.edition_id,
            public_name="Editor Verified",
            identity_status="verified",
            affiliation_status="active",
            source_url="https://example.test/authors/editor-verified",
        )

    def test_only_single_verified_active_affiliation_resolves(self) -> None:
        resolution = resolve_byline(self.document, (self.verified,))

        self.assertEqual("journalist_verified", resolution.journalist_id)
        self.assertEqual(BylineStatus.VERIFIED, resolution.byline_status)

    def test_unverified_byline_stays_at_edition_level(self) -> None:
        resolution = resolve_byline(
            self.document,
            (replace(self.verified, identity_status="unverified"),),
        )

        self.assertIsNone(resolution.journalist_id)
        self.assertEqual(BylineStatus.UNVERIFIED, resolution.byline_status)
        self.assertEqual("identity_not_verified", resolution.reason_code)

    def test_ambiguous_and_multiple_author_bylines_never_auto_merge(self) -> None:
        ambiguous = resolve_byline(
            self.document,
            (
                self.verified,
                replace(self.verified, journalist_id="journalist_second"),
            ),
        )
        multiple = resolve_byline(
            replace(self.document, author_text="Editor Verified and Editor Two"),
            (self.verified,),
        )

        self.assertIsNone(ambiguous.journalist_id)
        self.assertEqual("ambiguous_exact_match", ambiguous.reason_code)
        self.assertEqual(BylineStatus.MULTIPLE_AUTHORS, multiple.byline_status)


if __name__ == "__main__":
    unittest.main()
