"""Rights-aware, immutable local raw-envelope archive."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping, Optional

from tools.pr_intel.core_media.contracts import RightsLabel, stable_id


_METADATA_FIELDS = frozenset(
    {
        "title",
        "canonical_url",
        "submitted_url",
        "author_text",
        "published_at",
        "source_ref",
        "content_type_hint",
        "sponsorship_disclosure",
        "is_syndicated",
        "canonical_document_id",
    }
)
_EXCERPT_FIELDS = _METADATA_FIELDS | {"summary_excerpt", "content_excerpt"}
_DENIED_FIELDS = frozenset(
    {"credential", "credential_ref", "token", "password", "secret", "private_note"}
)


@dataclass(frozen=True)
class RawEnvelope:
    run_id: str
    source_id: str
    fetched_at: datetime
    rights_label: RightsLabel
    allowed_fields: tuple[str, ...]
    retention_days: Optional[int]
    records: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class ArchiveReceipt:
    envelope_id: str
    raw_object_ref: str
    payload_sha256: str
    record_count: int
    rights_label: RightsLabel
    retention_expires_at: str
    stored_fields: tuple[str, ...]


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sanitize_record(
    record: Mapping[str, object],
    envelope: RawEnvelope,
) -> dict[str, object]:
    allowed = set(envelope.allowed_fields) - _DENIED_FIELDS
    if envelope.rights_label == RightsLabel.METADATA_ONLY:
        allowed &= _METADATA_FIELDS
    elif envelope.rights_label == RightsLabel.EXCERPT_ONLY:
        allowed &= _EXCERPT_FIELDS

    sanitized: dict[str, object] = {}
    for field in sorted(allowed):
        if field not in record:
            continue
        value = record[field]
        if field in {"summary_excerpt", "content_excerpt"} and value is not None:
            value = " ".join(str(value).strip().split())[:500]
        sanitized[field] = value
    return sanitized


def archive_envelope(envelope: RawEnvelope, root: Path) -> ArchiveReceipt:
    if not envelope.run_id.strip() or not envelope.source_id.strip():
        raise ValueError("run_id_and_source_id_required")
    if envelope.fetched_at.tzinfo is None:
        raise ValueError("fetched_at_timezone_required")
    if envelope.retention_days is None:
        raise ValueError("retention_days_required")
    if envelope.retention_days < 1:
        raise ValueError("retention_days_invalid")

    original_json = _canonical_json(envelope.records)
    payload_sha256 = hashlib.sha256(original_json.encode("utf-8")).hexdigest()
    envelope_id = stable_id(
        "envelope",
        envelope.run_id,
        envelope.source_id,
        envelope.fetched_at.isoformat(),
        payload_sha256,
    )
    sanitized_records = tuple(
        _sanitize_record(record, envelope) for record in envelope.records
    )
    stored_fields = tuple(
        sorted({field for record in sanitized_records for field in record})
    )
    fetched_utc = envelope.fetched_at.astimezone(timezone.utc)
    expires_at = fetched_utc + timedelta(days=envelope.retention_days)
    archived = {
        "version": "1.0",
        "envelope_id": envelope_id,
        "run_id": envelope.run_id,
        "source_id": envelope.source_id,
        "fetched_at": fetched_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "payload_sha256": payload_sha256,
        "rights_label": envelope.rights_label.value,
        "retention_expires_at": expires_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "record_count": len(sanitized_records),
        "stored_fields": stored_fields,
        "records": sanitized_records,
    }
    serialized = json.dumps(
        archived,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ) + "\n"

    safe_source = stable_id("source", envelope.source_id)
    directory = (
        Path(root)
        / f"{fetched_utc.year:04d}"
        / f"{fetched_utc.month:02d}"
        / f"{fetched_utc.day:02d}"
        / safe_source
    )
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / f"{envelope_id}.json"
    if output.exists():
        if output.read_text(encoding="utf-8") != serialized:
            raise RuntimeError("archive_immutable_conflict")
    else:
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=f".{envelope_id}.",
            suffix=".tmp",
            delete=False,
        )
        temp_path = Path(handle.name)
        try:
            with handle:
                handle.write(serialized)
            os.replace(temp_path, output)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    return ArchiveReceipt(
        envelope_id=envelope_id,
        raw_object_ref=str(output),
        payload_sha256=payload_sha256,
        record_count=len(sanitized_records),
        rights_label=envelope.rights_label,
        retention_expires_at=archived["retention_expires_at"],
        stored_fields=stored_fields,
    )
