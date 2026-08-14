"""PR 核心媒体 P0 的稳定枚举、错误和 ID 合同。"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class CoverageStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NO_MATCH = "no_match"
    SOURCE_UNAVAILABLE = "source_unavailable"
    RATE_LIMITED = "rate_limited"
    SCHEMA_CHANGED = "schema_changed"
    PROFILE_INVALID = "profile_invalid"
    PERMISSION_PENDING = "permission_pending"
    UNKNOWN = "unknown"


class PermissionStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    BLOCKED = "blocked"
    MANUAL_ONLY = "manual_only"


class RightsLabel(str, Enum):
    FULL_TEXT_ALLOWED = "full_text_allowed"
    EXCERPT_ONLY = "excerpt_only"
    METADATA_ONLY = "metadata_only"


class BylineStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    MULTIPLE_AUTHORS = "multiple_authors"
    OUTLET_ONLY = "outlet_only"
    NO_BYLINE = "no_byline"


class ReviewStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    APPROVED = "approved"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ContractViolation:
    code: str
    field: str
    message: str


_PREFIX_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def normalize_id_part(value: str) -> str:
    """Normalize identity input without collapsing semantically distinct parts."""
    normalized = unicodedata.normalize("NFKC", str(value))
    return " ".join(normalized.strip().split()).casefold()


def stable_id(prefix: str, *parts: str, length: int = 16) -> str:
    """Return a deterministic, namespaced SHA-256 identifier."""
    if not _PREFIX_RE.fullmatch(prefix):
        raise ValueError("prefix must match ^[a-z][a-z0-9_]*$")
    if length < 8 or length > 64:
        raise ValueError("length must be between 8 and 64")
    if not parts:
        raise ValueError("at least one identity part is required")

    normalized_parts = [normalize_id_part(part) for part in parts]
    if any(not part for part in normalized_parts):
        raise ValueError("identity parts must be non-empty after normalization")
    payload = "\x1f".join(normalized_parts).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:length]
    return f"{prefix}_{digest}"
