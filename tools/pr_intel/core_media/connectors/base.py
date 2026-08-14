"""Source capability registry, policy gate, and network-free preflight."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from tools.pr_intel.core_media.contracts import (
    PermissionStatus,
    RightsLabel,
    normalize_id_part,
)
from tools.pr_intel.core_media.scope_loader import P0Scope


_COLLECTION_METHODS = frozenset({"rss", "author_page", "manual_url"})
_ACCESS_STATUSES = frozenset(
    {"untested", "edition_unverified", "ready", "blocked"}
)


class CollectionBlocked(RuntimeError):
    def __init__(self, code: str, source_id: str) -> None:
        super().__init__(f"{code}: {source_id}")
        self.code = code
        self.source_id = source_id


@dataclass(frozen=True)
class SourceCapability:
    version: str
    source_id: str
    outlet_name: str
    outlet_id: str
    edition_id: str
    source_type: str
    collection_method: str
    entrypoint: Optional[str]
    permission_status: PermissionStatus
    permission_evidence_ref: str
    rights_label: RightsLabel
    allowed_fields: tuple[str, ...]
    retention_days: Optional[int]
    collection_frequency: str
    historical_window_days: int
    credential_ref: Optional[str]
    access_status: str
    last_tested_at: Optional[str]
    last_success_at: Optional[str]
    fallback_method: str
    fallback_source_id: Optional[str]
    owner_role: str
    reviewer_role: str
    selectors: tuple[tuple[str, str], ...] = ()
    tracking_query_keys: tuple[str, ...] = ()

    def selector_map(self) -> dict[str, str]:
        return dict(self.selectors)


@dataclass(frozen=True)
class CollectionRequest:
    source_id: str
    edition_id: str
    requested_start: datetime
    requested_end: datetime
    purpose: str
    offline: bool
    manual_submission: bool


@dataclass(frozen=True)
class CollectedRecord:
    canonical_url: str
    title: Optional[str]
    author_text: Optional[str]
    published_at: Optional[str]
    summary_excerpt: Optional[str]
    source_ref: str
    sponsorship_disclosure: Optional[str] = None
    is_syndicated: bool = False
    canonical_document_id: Optional[str] = None


@dataclass(frozen=True)
class ConnectorReviewItem:
    code: str
    source_ref: str
    message: str


@dataclass(frozen=True)
class CollectionResult:
    source_id: str
    edition_id: str
    coverage_status: "CoverageStatus"
    records: tuple[CollectedRecord, ...]
    review_items: tuple[ConnectorReviewItem, ...]
    items_seen: int
    items_accepted: int
    error_code: Optional[str]
    safe_error_message: Optional[str]
    retry_after_seconds: Optional[int]
    fetched_at: str
    raw_object_ref: Optional[str] = None


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes
    final_url: str


class TransportFailure(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.safe_message = message


class UrllibTransport:
    """Small bounded HTTP transport; callers must run the permission gate first."""

    def __init__(self, *, timeout_seconds: float = 10.0, max_bytes: int = 2_000_000) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def get(self, url: str) -> HttpResponse:
        request = Request(
            url,
            headers={"User-Agent": "Momcozy-PR-Core-Media-P0/1.0"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read(self.max_bytes + 1)
                if len(body) > self.max_bytes:
                    raise TransportFailure(
                        "response_too_large", "Response exceeded configured byte limit"
                    )
                return HttpResponse(
                    status_code=int(response.status),
                    headers=dict(response.headers.items()),
                    body=body,
                    final_url=str(response.geturl()),
                )
        except HTTPError as exc:
            body = exc.read(self.max_bytes + 1)
            if len(body) > self.max_bytes:
                body = b""
            return HttpResponse(
                status_code=int(exc.code),
                headers=dict(exc.headers.items()) if exc.headers else {},
                body=body,
                final_url=str(exc.geturl()),
            )
        except URLError as exc:
            raise TransportFailure(
                "network_error", f"HTTP request failed ({type(exc.reason).__name__})"
            ) from exc


@dataclass(frozen=True)
class OutletCapabilityStatus:
    outlet_name: str
    edition_status: str
    source_ids: tuple[str, ...]
    permission_statuses: tuple[str, ...]
    has_manual_fallback: bool


@dataclass(frozen=True)
class CapabilityAudit:
    total_scope_outlets: int
    covered_scope_outlets: int
    automatic_capabilities: int
    manual_capabilities: int
    outlet_statuses: tuple[OutletCapabilityStatus, ...]
    outlets_without_capability: tuple[str, ...]
    outlets_without_manual_fallback: tuple[str, ...]
    unknown_outlet_names: tuple[str, ...]
    duplicate_source_ids: tuple[str, ...]
    pending_permission_sources: tuple[str, ...]
    manual_only_sources: tuple[str, ...]
    blocked_sources: tuple[str, ...]
    missing_permission_evidence: tuple[str, ...]
    rights_field_conflicts: tuple[str, ...]
    missing_retention_sources: tuple[str, ...]
    missing_owner_sources: tuple[str, ...]
    missing_reviewer_sources: tuple[str, ...]
    fallback_reference_errors: tuple[str, ...]
    live_readonly_smoke_allowed: bool
    offline_validation: bool
    network_requests_made: int

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": {
                "total_scope_outlets": self.total_scope_outlets,
                "covered_scope_outlets": self.covered_scope_outlets,
                "automatic_capabilities": self.automatic_capabilities,
                "manual_capabilities": self.manual_capabilities,
                "live_readonly_smoke_allowed": self.live_readonly_smoke_allowed,
                "offline_validation": self.offline_validation,
                "network_requests_made": self.network_requests_made,
            },
            "outlets": [asdict(item) for item in self.outlet_statuses],
            "issues": {
                "outlets_without_capability": list(self.outlets_without_capability),
                "outlets_without_manual_fallback": list(
                    self.outlets_without_manual_fallback
                ),
                "unknown_outlet_names": list(self.unknown_outlet_names),
                "duplicate_source_ids": list(self.duplicate_source_ids),
                "pending_permission_sources": list(
                    self.pending_permission_sources
                ),
                "manual_only_sources": list(self.manual_only_sources),
                "blocked_sources": list(self.blocked_sources),
                "missing_permission_evidence": list(
                    self.missing_permission_evidence
                ),
                "rights_field_conflicts": list(self.rights_field_conflicts),
                "missing_retention_sources": list(
                    self.missing_retention_sources
                ),
                "missing_owner_sources": list(self.missing_owner_sources),
                "missing_reviewer_sources": list(self.missing_reviewer_sources),
                "fallback_reference_errors": list(
                    self.fallback_reference_errors
                ),
            },
        }


def _required_text(data: Mapping[str, object], field: str, index: int) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"capabilities.{index}.{field}_required")
    return value.strip()


def _optional_text(data: Mapping[str, object], field: str, index: int) -> Optional[str]:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"capabilities.{index}.{field}_invalid")
    return value.strip()


def _parse_capability(data: Mapping[str, object], index: int) -> SourceCapability:
    method = _required_text(data, "collection_method", index)
    if method not in _COLLECTION_METHODS:
        raise ValueError(f"capabilities.{index}.collection_method_invalid")
    entrypoint = _optional_text(data, "entrypoint", index)
    if method == "rss" and entrypoint is None:
        raise ValueError(f"capabilities.{index}.entrypoint_required")

    try:
        permission_status = PermissionStatus(
            _required_text(data, "permission_status", index)
        )
    except ValueError as exc:
        raise ValueError(
            f"capabilities.{index}.permission_status_invalid"
        ) from exc
    try:
        rights_label = RightsLabel(_required_text(data, "rights_label", index))
    except ValueError as exc:
        raise ValueError(f"capabilities.{index}.rights_label_invalid") from exc

    allowed_fields = data.get("allowed_fields")
    if (
        not isinstance(allowed_fields, list)
        or not allowed_fields
        or any(not isinstance(item, str) or not item.strip() for item in allowed_fields)
    ):
        raise ValueError(f"capabilities.{index}.allowed_fields_invalid")

    retention = data.get("retention_days")
    if retention is not None and (
        not isinstance(retention, int)
        or isinstance(retention, bool)
        or retention < 1
    ):
        raise ValueError(f"capabilities.{index}.retention_days_invalid")

    historical = data.get("historical_window_days")
    if (
        not isinstance(historical, int)
        or isinstance(historical, bool)
        or historical < 1
        or historical > 180
    ):
        raise ValueError(f"capabilities.{index}.historical_window_days_invalid")

    credential_ref = _optional_text(data, "credential_ref", index)
    if credential_ref is not None and not credential_ref.startswith("secret_ref:"):
        raise ValueError("credential_ref_must_be_secret_ref")

    access_status = _required_text(data, "access_status", index)
    if access_status not in _ACCESS_STATUSES:
        raise ValueError(f"capabilities.{index}.access_status_invalid")

    raw_selectors = data.get("selectors", {})
    if not isinstance(raw_selectors, Mapping) or any(
        not isinstance(key, str)
        or not key.strip()
        or not isinstance(value, str)
        or not value.strip()
        for key, value in raw_selectors.items()
    ):
        raise ValueError(f"capabilities.{index}.selectors_invalid")
    raw_tracking_keys = data.get("tracking_query_keys", [])
    if not isinstance(raw_tracking_keys, list) or any(
        not isinstance(value, str) or not value.strip()
        for value in raw_tracking_keys
    ):
        raise ValueError(f"capabilities.{index}.tracking_query_keys_invalid")

    return SourceCapability(
        version=_required_text(data, "version", index),
        source_id=_required_text(data, "source_id", index),
        outlet_name=_required_text(data, "outlet_name", index),
        outlet_id=_required_text(data, "outlet_id", index),
        edition_id=_required_text(data, "edition_id", index),
        source_type=_required_text(data, "source_type", index),
        collection_method=method,
        entrypoint=entrypoint,
        permission_status=permission_status,
        permission_evidence_ref=_required_text(
            data, "permission_evidence_ref", index
        ),
        rights_label=rights_label,
        allowed_fields=tuple(item.strip() for item in allowed_fields),
        retention_days=retention,
        collection_frequency=_required_text(
            data, "collection_frequency", index
        ),
        historical_window_days=historical,
        credential_ref=credential_ref,
        access_status=access_status,
        last_tested_at=_optional_text(data, "last_tested_at", index),
        last_success_at=_optional_text(data, "last_success_at", index),
        fallback_method=_required_text(data, "fallback_method", index),
        fallback_source_id=_optional_text(data, "fallback_source_id", index),
        owner_role=_required_text(data, "owner_role", index),
        reviewer_role=_required_text(data, "reviewer_role", index),
        selectors=tuple(
            sorted((key.strip(), value.strip()) for key, value in raw_selectors.items())
        ),
        tracking_query_keys=tuple(
            sorted({value.strip().casefold() for value in raw_tracking_keys})
        ),
    )


def load_capabilities(path: Path) -> tuple[SourceCapability, ...]:
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    raw_capabilities = data.get("capabilities") if isinstance(data, Mapping) else None
    defaults = data.get("defaults", {}) if isinstance(data, Mapping) else {}
    if not isinstance(defaults, Mapping):
        raise ValueError("capability_defaults_must_be_object")
    if not isinstance(raw_capabilities, list):
        raise ValueError("capabilities_array_required")
    merged_records: list[Mapping[str, object]] = []
    for item in raw_capabilities:
        if not isinstance(item, Mapping):
            raise ValueError("capability_record_must_be_object")
        merged_records.append({**defaults, **item})
    parsed = tuple(
        _parse_capability(item, index)
        for index, item in enumerate(merged_records)
    )
    source_ids = [item.source_id for item in parsed]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate_source_id")
    return parsed


def validate_capabilities(
    scope: P0Scope,
    capabilities: Sequence[SourceCapability],
    *,
    offline: bool,
) -> CapabilityAudit:
    by_outlet: dict[str, list[SourceCapability]] = {}
    scope_name_by_key = {
        normalize_id_part(item.canonical_name): item.canonical_name
        for item in scope.outlets
    }
    duplicate_ids: list[str] = []
    seen_ids: set[str] = set()
    for item in capabilities:
        if item.source_id in seen_ids:
            duplicate_ids.append(item.source_id)
        seen_ids.add(item.source_id)
        by_outlet.setdefault(normalize_id_part(item.outlet_name), []).append(item)

    missing_capability: list[str] = []
    missing_manual: list[str] = []
    statuses: list[OutletCapabilityStatus] = []
    for outlet in scope.outlets:
        key = normalize_id_part(outlet.canonical_name)
        items = by_outlet.get(key, [])
        if not items:
            missing_capability.append(outlet.canonical_name)
        has_manual = any(item.collection_method == "manual_url" for item in items)
        if not has_manual:
            missing_manual.append(outlet.canonical_name)
        statuses.append(
            OutletCapabilityStatus(
                outlet_name=outlet.canonical_name,
                edition_status=outlet.edition_status,
                source_ids=tuple(sorted(item.source_id for item in items)),
                permission_statuses=tuple(
                    sorted({item.permission_status.value for item in items})
                ),
                has_manual_fallback=has_manual,
            )
        )

    by_source_id = {item.source_id: item for item in capabilities}
    fallback_errors: list[str] = []
    for item in capabilities:
        if item.collection_method == "manual_url":
            continue
        fallback = by_source_id.get(item.fallback_source_id or "")
        if (
            fallback is None
            or fallback.collection_method != "manual_url"
            or normalize_id_part(fallback.outlet_name)
            != normalize_id_part(item.outlet_name)
        ):
            fallback_errors.append(item.source_id)

    pending = tuple(
        sorted(
            item.source_id
            for item in capabilities
            if item.permission_status == PermissionStatus.PENDING
        )
    )
    manual_only = tuple(
        sorted(
            item.source_id
            for item in capabilities
            if item.permission_status == PermissionStatus.MANUAL_ONLY
        )
    )
    blocked = tuple(
        sorted(
            item.source_id
            for item in capabilities
            if item.permission_status == PermissionStatus.BLOCKED
        )
    )
    missing_evidence = tuple(
        sorted(
            item.source_id
            for item in capabilities
            if not item.permission_evidence_ref.strip()
        )
    )
    full_text_fields = {"full_text", "content_text", "body", "raw_html"}
    excerpt_fields = full_text_fields | {"summary_excerpt", "content_excerpt"}
    rights_conflicts = tuple(
        sorted(
            item.source_id
            for item in capabilities
            if (
                item.rights_label == RightsLabel.METADATA_ONLY
                and bool(set(item.allowed_fields) & excerpt_fields)
            )
            or (
                item.rights_label == RightsLabel.EXCERPT_ONLY
                and bool(set(item.allowed_fields) & full_text_fields)
            )
        )
    )
    missing_retention = tuple(
        sorted(
            item.source_id
            for item in capabilities
            if item.retention_days is None
        )
    )
    missing_owner = tuple(
        sorted(item.source_id for item in capabilities if not item.owner_role.strip())
    )
    missing_reviewer = tuple(
        sorted(
            item.source_id for item in capabilities if not item.reviewer_role.strip()
        )
    )
    unknown_outlets = tuple(
        sorted(
            item.outlet_name
            for item in capabilities
            if normalize_id_part(item.outlet_name) not in scope_name_by_key
        )
    )

    automatic = tuple(
        item for item in capabilities if item.collection_method != "manual_url"
    )
    live_allowed = (
        scope.status == "approved"
        and all(item.edition_status == "verified" for item in scope.outlets)
        and not missing_capability
        and not fallback_errors
        and not pending
        and not blocked
        and not missing_evidence
        and not rights_conflicts
        and not missing_retention
        and not missing_owner
        and not missing_reviewer
        and bool(automatic)
        and all(
            item.permission_status == PermissionStatus.APPROVED
            and item.access_status in {"untested", "ready"}
            for item in automatic
        )
    )

    return CapabilityAudit(
        total_scope_outlets=len(scope.outlets),
        covered_scope_outlets=len(scope.outlets) - len(missing_capability),
        automatic_capabilities=len(automatic),
        manual_capabilities=sum(
            item.collection_method == "manual_url" for item in capabilities
        ),
        outlet_statuses=tuple(statuses),
        outlets_without_capability=tuple(missing_capability),
        outlets_without_manual_fallback=tuple(missing_manual),
        unknown_outlet_names=unknown_outlets,
        duplicate_source_ids=tuple(sorted(set(duplicate_ids))),
        pending_permission_sources=pending,
        manual_only_sources=manual_only,
        blocked_sources=blocked,
        missing_permission_evidence=missing_evidence,
        rights_field_conflicts=rights_conflicts,
        missing_retention_sources=missing_retention,
        missing_owner_sources=missing_owner,
        missing_reviewer_sources=missing_reviewer,
        fallback_reference_errors=tuple(sorted(fallback_errors)),
        live_readonly_smoke_allowed=live_allowed,
        offline_validation=offline,
        network_requests_made=0,
    )


def assert_collection_allowed(
    capability: SourceCapability,
    request: CollectionRequest,
) -> None:
    if request.source_id != capability.source_id:
        raise CollectionBlocked("source_id_mismatch", capability.source_id)
    if request.edition_id != capability.edition_id:
        raise CollectionBlocked("edition_id_mismatch", capability.source_id)
    if request.requested_start >= request.requested_end:
        raise CollectionBlocked("invalid_collection_window", capability.source_id)

    permission = capability.permission_status
    if permission == PermissionStatus.PENDING:
        raise CollectionBlocked("permission_pending", capability.source_id)
    if permission == PermissionStatus.BLOCKED:
        raise CollectionBlocked("permission_blocked", capability.source_id)
    if permission == PermissionStatus.MANUAL_ONLY:
        if (
            capability.collection_method != "manual_url"
            or not request.manual_submission
            or not request.offline
        ):
            raise CollectionBlocked(
                "manual_submission_required", capability.source_id
            )
        return

    if capability.access_status == "blocked":
        raise CollectionBlocked("source_access_blocked", capability.source_id)
    if capability.collection_method == "manual_url" and (
        not request.manual_submission or not request.offline
    ):
        raise CollectionBlocked("manual_submission_required", capability.source_id)
