"""Strict byline resolution; ambiguous or unverified authors stay edition-level."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence
from urllib.parse import urlparse

from tools.pr_intel.core_media.contracts import BylineStatus, normalize_id_part
from tools.pr_intel.core_media.normalizer import Document


_MULTI_AUTHOR_RE = re.compile(r"\s(?:and|&)\s|[;|]", re.IGNORECASE)


@dataclass(frozen=True)
class JournalistAffiliation:
    journalist_id: str
    edition_id: str
    public_name: str
    identity_status: str
    affiliation_status: str
    source_url: Optional[str]


@dataclass(frozen=True)
class BylineResolution:
    journalist_id: Optional[str]
    byline_status: BylineStatus
    candidate_ids: tuple[str, ...]
    reason_code: str


def _author_key(value: str) -> str:
    stripped = re.sub(r"^\s*by\s+", "", value, flags=re.IGNORECASE)
    return normalize_id_part(stripped)


def _valid_source_url(value: Optional[str]) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme.casefold() in {"http", "https"} and bool(parsed.netloc)


def resolve_byline(
    document: Document,
    affiliations: Sequence[JournalistAffiliation],
) -> BylineResolution:
    author_text = document.author_text
    if not author_text or not author_text.strip():
        return BylineResolution(None, BylineStatus.NO_BYLINE, (), "byline_missing")
    if _MULTI_AUTHOR_RE.search(author_text.strip()):
        return BylineResolution(
            None,
            BylineStatus.MULTIPLE_AUTHORS,
            (),
            "multiple_authors_require_review",
        )

    author_key = _author_key(author_text)
    matches = tuple(
        item
        for item in affiliations
        if item.edition_id == document.edition_id
        and _author_key(item.public_name) == author_key
    )
    candidate_ids = tuple(sorted({item.journalist_id for item in matches}))
    if not matches:
        return BylineResolution(
            None, BylineStatus.UNVERIFIED, (), "no_exact_affiliation_match"
        )
    if len(candidate_ids) != 1 or len(matches) != 1:
        return BylineResolution(
            None,
            BylineStatus.UNVERIFIED,
            candidate_ids,
            "ambiguous_exact_match",
        )

    match = matches[0]
    if match.identity_status != "verified":
        return BylineResolution(
            None,
            BylineStatus.UNVERIFIED,
            candidate_ids,
            "identity_not_verified",
        )
    if match.affiliation_status != "active":
        return BylineResolution(
            None,
            BylineStatus.UNVERIFIED,
            candidate_ids,
            "affiliation_not_active",
        )
    if not _valid_source_url(match.source_url):
        return BylineResolution(
            None,
            BylineStatus.UNVERIFIED,
            candidate_ids,
            "affiliation_evidence_missing",
        )
    return BylineResolution(
        match.journalist_id,
        BylineStatus.VERIFIED,
        candidate_ids,
        "verified_exact_match",
    )
