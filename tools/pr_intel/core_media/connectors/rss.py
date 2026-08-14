"""Permission-gated RSS connector with structured coverage outcomes."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import feedparser

from tools.pr_intel.core_media.connectors.base import (
    CollectedRecord,
    CollectionRequest,
    CollectionResult,
    ConnectorReviewItem,
    SourceCapability,
    TransportFailure,
    UrllibTransport,
    assert_collection_allowed,
)
from tools.pr_intel.core_media.contracts import CoverageStatus, RightsLabel


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _valid_http_url(value: object) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
        return None
    return value.strip()


def _retry_after(headers: object) -> Optional[int]:
    if not hasattr(headers, "get"):
        return None
    value = headers.get("Retry-After")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _summary(
    capability: SourceCapability,
    value: object,
) -> Optional[str]:
    if capability.rights_label == RightsLabel.METADATA_ONLY:
        return None
    if "summary_excerpt" not in capability.allowed_fields:
        return None
    text = " ".join(str(value or "").strip().split())
    return text[:500] or None


class RssConnector:
    def __init__(
        self,
        capability: SourceCapability,
        *,
        transport: Optional[UrllibTransport] = None,
    ) -> None:
        if capability.collection_method != "rss":
            raise ValueError("rss_capability_required")
        self.capability = capability
        self.transport = transport or UrllibTransport()

    def collect(self, request: CollectionRequest) -> CollectionResult:
        assert_collection_allowed(self.capability, request)
        if not self.capability.entrypoint:
            raise ValueError("rss_entrypoint_required")

        try:
            response = self.transport.get(self.capability.entrypoint)
        except TransportFailure as exc:
            return CollectionResult(
                source_id=self.capability.source_id,
                edition_id=self.capability.edition_id,
                coverage_status=CoverageStatus.SOURCE_UNAVAILABLE,
                records=(),
                review_items=(),
                items_seen=0,
                items_accepted=0,
                error_code=exc.code,
                safe_error_message=exc.safe_message,
                retry_after_seconds=None,
                fetched_at=_now(),
            )

        if response.status_code == 429:
            return self._http_error(
                CoverageStatus.RATE_LIMITED,
                "http_429_rate_limited",
                response.status_code,
                _retry_after(response.headers),
            )
        if response.status_code == 403:
            return self._http_error(
                CoverageStatus.SOURCE_UNAVAILABLE,
                "http_403_forbidden",
                response.status_code,
                None,
            )
        if response.status_code >= 400:
            return self._http_error(
                CoverageStatus.SOURCE_UNAVAILABLE,
                f"http_{response.status_code}",
                response.status_code,
                None,
            )

        parsed = feedparser.parse(response.body)
        entries = tuple(parsed.entries)
        if getattr(parsed, "bozo", False) and not entries:
            return CollectionResult(
                source_id=self.capability.source_id,
                edition_id=self.capability.edition_id,
                coverage_status=CoverageStatus.SCHEMA_CHANGED,
                records=(),
                review_items=(),
                items_seen=0,
                items_accepted=0,
                error_code="rss_parse_failed",
                safe_error_message="RSS payload could not be parsed into entries",
                retry_after_seconds=None,
                fetched_at=_now(),
            )
        if not entries:
            return CollectionResult(
                source_id=self.capability.source_id,
                edition_id=self.capability.edition_id,
                coverage_status=CoverageStatus.NO_MATCH,
                records=(),
                review_items=(),
                items_seen=0,
                items_accepted=0,
                error_code=None,
                safe_error_message=None,
                retry_after_seconds=None,
                fetched_at=_now(),
            )

        records: list[CollectedRecord] = []
        review: list[ConnectorReviewItem] = []
        seen_urls: set[str] = set()
        for index, entry in enumerate(entries):
            source_ref = f"feed_entry:{index}"
            url = _valid_http_url(entry.get("link"))
            if url is None:
                review.append(
                    ConnectorReviewItem(
                        "invalid_url", source_ref, "Entry has no valid canonical URL"
                    )
                )
                continue
            if url in seen_urls:
                review.append(
                    ConnectorReviewItem(
                        "duplicate_url", source_ref, "Duplicate canonical URL skipped"
                    )
                )
                continue
            seen_urls.add(url)
            published_at = entry.get("published") or entry.get("updated") or None
            if not published_at:
                review.append(
                    ConnectorReviewItem(
                        "published_at_missing",
                        source_ref,
                        "Entry accepted with unknown publication time",
                    )
                )
            records.append(
                CollectedRecord(
                    canonical_url=url,
                    title=(
                        " ".join(str(entry.get("title") or "").strip().split()) or None
                        if "title" in self.capability.allowed_fields
                        else None
                    ),
                    author_text=(
                        " ".join(str(entry.get("author") or "").strip().split()) or None
                        if "author_text" in self.capability.allowed_fields
                        else None
                    ),
                    published_at=(
                        str(published_at) if "published_at" in self.capability.allowed_fields and published_at else None
                    ),
                    summary_excerpt=_summary(
                        self.capability,
                        entry.get("summary") or entry.get("description"),
                    ),
                    source_ref=source_ref,
                )
            )

        status = CoverageStatus.PARTIAL if review else CoverageStatus.COMPLETE
        return CollectionResult(
            source_id=self.capability.source_id,
            edition_id=self.capability.edition_id,
            coverage_status=status,
            records=tuple(records),
            review_items=tuple(review),
            items_seen=len(entries),
            items_accepted=len(records),
            error_code=None,
            safe_error_message=None,
            retry_after_seconds=None,
            fetched_at=_now(),
        )

    def _http_error(
        self,
        status: CoverageStatus,
        code: str,
        http_status: int,
        retry_after: Optional[int],
    ) -> CollectionResult:
        return CollectionResult(
            source_id=self.capability.source_id,
            edition_id=self.capability.edition_id,
            coverage_status=status,
            records=(),
            review_items=(),
            items_seen=0,
            items_accepted=0,
            error_code=code,
            safe_error_message=f"Source returned HTTP {http_status}",
            retry_after_seconds=retry_after,
            fetched_at=_now(),
        )
