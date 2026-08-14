"""Deterministic PR core-media document normalization."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from tools.pr_intel.core_media.connectors.base import (
    CollectedRecord,
    CollectionResult,
    SourceCapability,
)
from tools.pr_intel.core_media.contracts import BylineStatus, stable_id


_CONTENT_TYPES = frozenset(
    {"review", "listicle", "news", "feature", "opinion", "social_post", "unknown"}
)
_SPONSORSHIP_STATUSES = frozenset(
    {"editorial", "sponsored", "affiliate", "syndicated", "unknown"}
)
_MULTI_AUTHOR_RE = re.compile(r"\s(?:and|&)\s|[;|]", re.IGNORECASE)


@dataclass(frozen=True)
class Document:
    version: str
    document_id: str
    source_id: str
    edition_id: str
    canonical_url: str
    published_at: Optional[str]
    fetched_at: str
    title: Optional[str]
    author_text: Optional[str]
    journalist_id: Optional[str]
    byline_status: BylineStatus
    content_type: str
    sponsorship_status: str
    text_hash: str
    rights_label: str
    is_syndicated: bool
    canonical_document_id: Optional[str]
    deletion_status: str
    raw_object_ref: str
    quality_issues: tuple[str, ...]
    trend_eligible: bool
    created_at: str
    updated_at: str


def canonicalize_url(url: str, tracking_query_keys: tuple[str, ...]) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.casefold() not in {"http", "https"} or not parts.hostname:
        raise ValueError("invalid_url")
    if parts.username or parts.password:
        raise ValueError("url_credentials_not_allowed")
    hostname = parts.hostname.casefold()
    port = parts.port
    netloc = hostname
    if port and not (
        (parts.scheme.casefold() == "http" and port == 80)
        or (parts.scheme.casefold() == "https" and port == 443)
    ):
        netloc = f"{hostname}:{port}"
    remove = {key.casefold() for key in tracking_query_keys}
    query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key.casefold() not in remove
        ],
        doseq=True,
    )
    return urlunsplit((parts.scheme.casefold(), netloc, parts.path or "/", query, ""))


def _timestamp(value: Optional[str]) -> Optional[str]:
    if value is None or not str(value).strip():
        return None
    raw = str(value).strip()
    parsed: Optional[datetime] = None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        return None
    return (
        parsed.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _content_type(record: CollectedRecord) -> str:
    title = (record.title or "").casefold()
    if re.search(r"\b(review|reviewed|tested|test)\b", title):
        value = "review"
    elif re.search(r"\b(best|top\s+\d+|\d+\s+best)\b", title):
        value = "listicle"
    elif re.search(r"\b(launch|announc|recall|news)\w*\b", title):
        value = "news"
    elif re.search(r"\b(opinion|why i|commentary)\b", title):
        value = "opinion"
    elif re.search(r"\b(feature|guide|how to)\b", title):
        value = "feature"
    else:
        value = "unknown"
    if value not in _CONTENT_TYPES:
        raise AssertionError("content_type_contract_broken")
    return value


def _sponsorship(record: CollectedRecord) -> str:
    if record.is_syndicated:
        return "syndicated"
    evidence = (record.sponsorship_disclosure or "").casefold()
    if re.search(r"\b(sponsored|paid partnership|partner content|advertorial)\b", evidence):
        value = "sponsored"
    elif re.search(r"\b(affiliate|commission|may earn)\b", evidence):
        value = "affiliate"
    else:
        value = "unknown"
    if value not in _SPONSORSHIP_STATUSES:
        raise AssertionError("sponsorship_status_contract_broken")
    return value


def _initial_byline(author_text: Optional[str]) -> BylineStatus:
    if not author_text or not author_text.strip():
        return BylineStatus.NO_BYLINE
    if _MULTI_AUTHOR_RE.search(author_text.strip()):
        return BylineStatus.MULTIPLE_AUTHORS
    return BylineStatus.UNVERIFIED


def _text_hash(record: CollectedRecord, canonical_url: str) -> str:
    normalized = "\x1f".join(
        " ".join(str(value or "").strip().split()).casefold()
        for value in (
            canonical_url,
            record.title,
            record.author_text,
            record.summary_excerpt,
        )
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_records(
    result: CollectionResult,
    capability: SourceCapability,
) -> tuple[Document, ...]:
    if result.source_id != capability.source_id:
        raise ValueError("source_id_mismatch")
    if result.edition_id != capability.edition_id:
        raise ValueError("edition_id_mismatch")
    if not result.raw_object_ref:
        raise ValueError("raw_object_ref_required")
    fetched_at = _timestamp(result.fetched_at)
    if fetched_at is None:
        raise ValueError("fetched_at_invalid")

    documents: list[Document] = []
    seen_hashes: set[str] = set()
    for record in result.records:
        issues: list[str] = []
        try:
            canonical_url = canonicalize_url(
                record.canonical_url, capability.tracking_query_keys
            )
        except ValueError as exc:
            canonical_url = record.canonical_url.strip()
            issues.append(str(exc))
        published_at = _timestamp(record.published_at)
        if published_at is None:
            issues.append("invalid_timestamp")
        sponsorship = _sponsorship(record)
        if record.is_syndicated and not record.canonical_document_id:
            issues.append("syndication_canonical_missing")
        text_hash = _text_hash(record, canonical_url)
        if text_hash in seen_hashes:
            continue
        seen_hashes.add(text_hash)
        document_id = stable_id(
            "document",
            result.source_id,
            canonical_url,
            published_at or "invalid_timestamp",
            text_hash,
        )
        trend_eligible = not issues
        documents.append(
            Document(
                version="1.1",
                document_id=document_id,
                source_id=result.source_id,
                edition_id=result.edition_id,
                canonical_url=canonical_url,
                published_at=published_at,
                fetched_at=fetched_at,
                title=record.title,
                author_text=record.author_text,
                journalist_id=None,
                byline_status=_initial_byline(record.author_text),
                content_type=_content_type(record),
                sponsorship_status=sponsorship,
                text_hash=text_hash,
                rights_label=capability.rights_label.value,
                is_syndicated=record.is_syndicated,
                canonical_document_id=record.canonical_document_id,
                deletion_status="active",
                raw_object_ref=result.raw_object_ref,
                quality_issues=tuple(sorted(set(issues))),
                trend_eligible=trend_eligible,
                created_at=fetched_at,
                updated_at=fetched_at,
            )
        )
    return tuple(documents)
