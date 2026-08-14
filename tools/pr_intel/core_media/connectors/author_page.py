"""Permission-gated author-page connector using declared selectors only."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

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
from tools.pr_intel.core_media.contracts import CoverageStatus


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class AuthorPageConnector:
    def __init__(
        self,
        capability: SourceCapability,
        *,
        transport: Optional[UrllibTransport] = None,
    ) -> None:
        if capability.collection_method != "author_page":
            raise ValueError("author_page_capability_required")
        self.capability = capability
        self.transport = transport or UrllibTransport()

    def collect(self, request: CollectionRequest) -> CollectionResult:
        assert_collection_allowed(self.capability, request)
        selectors = self.capability.selector_map()
        if not self.capability.entrypoint or not selectors.get("item"):
            return self._error(
                CoverageStatus.SCHEMA_CHANGED,
                "author_selectors_missing",
                "Author page item selector is not configured",
            )
        try:
            response = self.transport.get(self.capability.entrypoint)
        except TransportFailure as exc:
            return self._error(
                CoverageStatus.SOURCE_UNAVAILABLE, exc.code, exc.safe_message
            )

        if response.status_code in {404, 410}:
            return self._error(
                CoverageStatus.PROFILE_INVALID,
                f"http_{response.status_code}_profile_invalid",
                f"Author page returned HTTP {response.status_code}",
            )
        if response.status_code == 429:
            return CollectionResult(
                source_id=self.capability.source_id,
                edition_id=self.capability.edition_id,
                coverage_status=CoverageStatus.RATE_LIMITED,
                records=(),
                review_items=(),
                items_seen=0,
                items_accepted=0,
                error_code="http_429_rate_limited",
                safe_error_message="Author page returned HTTP 429",
                retry_after_seconds=None,
                fetched_at=_now(),
            )
        if response.status_code >= 400:
            return self._error(
                CoverageStatus.SOURCE_UNAVAILABLE,
                f"http_{response.status_code}",
                f"Author page returned HTTP {response.status_code}",
            )

        soup = BeautifulSoup(response.body, "html.parser")
        nodes = tuple(soup.select(selectors["item"]))
        if not nodes:
            return self._error(
                CoverageStatus.SCHEMA_CHANGED,
                "author_selector_no_match",
                "Configured author-page item selector matched zero nodes",
            )

        records: list[CollectedRecord] = []
        review: list[ConnectorReviewItem] = []
        seen_urls: set[str] = set()
        for index, node in enumerate(nodes):
            source_ref = f"author_item:{index}"
            link_node = node.select_one(selectors.get("link", "")) if selectors.get("link") else None
            href = link_node.get("href") if link_node is not None else None
            url = urljoin(response.final_url, str(href or ""))
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                review.append(
                    ConnectorReviewItem(
                        "invalid_url", source_ref, "Author item has no valid URL"
                    )
                )
                continue
            if url in seen_urls:
                review.append(
                    ConnectorReviewItem(
                        "duplicate_url", source_ref, "Duplicate author item URL skipped"
                    )
                )
                continue
            seen_urls.add(url)

            title_node = node.select_one(selectors.get("title", "")) if selectors.get("title") else None
            author_node = node.select_one(selectors.get("author", "")) if selectors.get("author") else None
            date_node = node.select_one(selectors.get("published_at", "")) if selectors.get("published_at") else None
            published_at = None
            if date_node is not None:
                published_at = date_node.get("datetime") or date_node.get_text(" ", strip=True) or None
            if not published_at:
                review.append(
                    ConnectorReviewItem(
                        "published_at_missing",
                        source_ref,
                        "Author item accepted with unknown publication time",
                    )
                )
            records.append(
                CollectedRecord(
                    canonical_url=url,
                    title=(
                        title_node.get_text(" ", strip=True) or None
                        if title_node is not None and "title" in self.capability.allowed_fields
                        else None
                    ),
                    author_text=(
                        author_node.get_text(" ", strip=True) or None
                        if author_node is not None and "author_text" in self.capability.allowed_fields
                        else None
                    ),
                    published_at=(
                        str(published_at)
                        if published_at and "published_at" in self.capability.allowed_fields
                        else None
                    ),
                    summary_excerpt=None,
                    source_ref=source_ref,
                )
            )

        return CollectionResult(
            source_id=self.capability.source_id,
            edition_id=self.capability.edition_id,
            coverage_status=(
                CoverageStatus.PARTIAL if review else CoverageStatus.COMPLETE
            ),
            records=tuple(records),
            review_items=tuple(review),
            items_seen=len(nodes),
            items_accepted=len(records),
            error_code=None,
            safe_error_message=None,
            retry_after_seconds=None,
            fetched_at=_now(),
        )

    def _error(
        self, status: CoverageStatus, code: str, message: str
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
            safe_error_message=message,
            retry_after_seconds=None,
            fetched_at=_now(),
        )
