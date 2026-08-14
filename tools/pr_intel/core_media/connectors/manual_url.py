"""Manual URL connector: validates submitted metadata and never performs HTTP."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Optional, Sequence
from urllib.parse import urlparse

from tools.pr_intel.core_media.connectors.base import (
    CollectedRecord,
    CollectionRequest,
    CollectionResult,
    ConnectorReviewItem,
    SourceCapability,
    assert_collection_allowed,
)
from tools.pr_intel.core_media.contracts import CoverageStatus, RightsLabel


_RIGHTS_RANK = {
    RightsLabel.METADATA_ONLY: 0,
    RightsLabel.EXCERPT_ONLY: 1,
    RightsLabel.FULL_TEXT_ALLOWED: 2,
}


@dataclass(frozen=True)
class ManualSubmission:
    submitted_url: str
    edition_id: str
    submitted_by_role: str
    submitted_at: datetime
    rights_label: RightsLabel
    title: Optional[str] = None
    author_text: Optional[str] = None
    published_at: Optional[str] = None
    summary_excerpt: Optional[str] = None
    extra_fields: Mapping[str, object] = field(default_factory=dict)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ManualUrlConnector:
    def __init__(self, capability: SourceCapability) -> None:
        if capability.collection_method != "manual_url":
            raise ValueError("manual_url_capability_required")
        self.capability = capability

    def collect(
        self,
        request: CollectionRequest,
        submissions: Sequence[ManualSubmission],
    ) -> CollectionResult:
        assert_collection_allowed(self.capability, request)
        records: list[CollectedRecord] = []
        review: list[ConnectorReviewItem] = []
        seen_urls: set[str] = set()

        for index, submission in enumerate(submissions):
            source_ref = f"manual_submission:{index}"
            if submission.edition_id != self.capability.edition_id:
                review.append(
                    ConnectorReviewItem(
                        "edition_mismatch",
                        source_ref,
                        "Submission edition does not match the verified capability edition",
                    )
                )
                continue
            if not submission.submitted_by_role.strip():
                review.append(
                    ConnectorReviewItem(
                        "submitter_role_missing",
                        source_ref,
                        "Submission requires a responsible role",
                    )
                )
                continue
            if submission.submitted_at.tzinfo is None:
                review.append(
                    ConnectorReviewItem(
                        "submitted_at_timezone_missing",
                        source_ref,
                        "Submission timestamp must include timezone",
                    )
                )
                continue
            parsed = urlparse(submission.submitted_url)
            if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
                review.append(
                    ConnectorReviewItem(
                        "invalid_url", source_ref, "Submission URL is invalid"
                    )
                )
                continue
            if submission.submitted_url in seen_urls:
                review.append(
                    ConnectorReviewItem(
                        "duplicate_url", source_ref, "Duplicate submission URL skipped"
                    )
                )
                continue
            if _RIGHTS_RANK[submission.rights_label] > _RIGHTS_RANK[self.capability.rights_label]:
                review.append(
                    ConnectorReviewItem(
                        "rights_exceed_capability",
                        source_ref,
                        "Submission rights exceed the approved capability",
                    )
                )
                continue
            seen_urls.add(submission.submitted_url)
            summary = None
            if (
                submission.rights_label != RightsLabel.METADATA_ONLY
                and self.capability.rights_label != RightsLabel.METADATA_ONLY
                and "summary_excerpt" in self.capability.allowed_fields
            ):
                summary = (
                    " ".join((submission.summary_excerpt or "").strip().split())[:500]
                    or None
                )
            records.append(
                CollectedRecord(
                    canonical_url=submission.submitted_url,
                    title=(
                        submission.title
                        if "title" in self.capability.allowed_fields
                        else None
                    ),
                    author_text=(
                        submission.author_text
                        if "author_text" in self.capability.allowed_fields
                        else None
                    ),
                    published_at=(
                        submission.published_at
                        if "published_at" in self.capability.allowed_fields
                        else None
                    ),
                    summary_excerpt=summary,
                    source_ref=source_ref,
                )
            )

        if review:
            status = CoverageStatus.PARTIAL
        elif records:
            status = CoverageStatus.COMPLETE
        else:
            status = CoverageStatus.NO_MATCH
        return CollectionResult(
            source_id=self.capability.source_id,
            edition_id=self.capability.edition_id,
            coverage_status=status,
            records=tuple(records),
            review_items=tuple(review),
            items_seen=len(submissions),
            items_accepted=len(records),
            error_code=None,
            safe_error_message=None,
            retry_after_seconds=None,
            fetched_at=_now(),
        )
