"""Checkpointed PR core-media workflow with safe, resumable stage manifests."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Optional


STAGE_ORDER = (
    "scope_check",
    "source_check",
    "collect",
    "normalize",
    "quality_gate",
    "analyze",
    "relationship_gate",
    "brief",
    "export",
)
_RUN_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{2,127}$")


class StageExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class StageOutput:
    output_refs: tuple[str, ...]
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class StageRecord:
    name: str
    status: str
    attempts: int
    started_at: Optional[str]
    ended_at: Optional[str]
    input_hash: Optional[str]
    output_refs: tuple[str, ...]
    output_metadata: Mapping[str, object]
    error_code: Optional[str]


@dataclass(frozen=True)
class RunManifest:
    version: str
    run_id: str
    fixture_only: bool
    network_requests_made: int
    status: str
    stages: Mapping[str, StageRecord]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class StageExecutionResult:
    stage: str
    reused: bool
    output_refs: tuple[str, ...]
    output_metadata: Mapping[str, object]


def _iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("workflow_clock_must_be_timezone_aware")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _json_default(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return _iso(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    raise TypeError(f"workflow_input_not_serializable:{type(value).__name__}")


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    )


def _input_hash(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _safe_metadata(value: Mapping[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, item in value.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", str(key)):
            raise ValueError("workflow_metadata_key_invalid")
        if item is None or isinstance(item, (bool, int, float)):
            safe[str(key)] = item
        elif isinstance(item, str) and len(item) <= 200 and not re.search(
            r"(?i)(token|password|secret|authorization|cookie)", str(key)
        ):
            safe[str(key)] = item
        else:
            raise ValueError(f"workflow_metadata_value_not_safe:{key}")
    return safe


def _atomic_write(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp = Path(handle.name)
    try:
        with handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _record_to_dict(record: StageRecord) -> dict[str, object]:
    return {
        "name": record.name,
        "status": record.status,
        "attempts": record.attempts,
        "started_at": record.started_at,
        "ended_at": record.ended_at,
        "input_hash": record.input_hash,
        "output_refs": list(record.output_refs),
        "output_metadata": dict(record.output_metadata),
        "error_code": record.error_code,
    }


def manifest_to_dict(manifest: RunManifest) -> dict[str, object]:
    return {
        "version": manifest.version,
        "run_id": manifest.run_id,
        "fixture_only": manifest.fixture_only,
        "network_requests_made": manifest.network_requests_made,
        "status": manifest.status,
        "stages": {
            stage: _record_to_dict(manifest.stages[stage]) for stage in STAGE_ORDER
        },
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
    }


class RunManifestStore:
    def __init__(
        self,
        path: Path,
        *,
        run_id: str,
        fixture_only: bool,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if not _RUN_ID_RE.fullmatch(run_id):
            raise ValueError("run_id_invalid")
        self.path = Path(path)
        self.run_id = run_id
        self.fixture_only = fixture_only
        self.clock = clock
        if self.path.exists():
            manifest = self.load()
            if manifest.run_id != run_id or manifest.fixture_only != fixture_only:
                raise ValueError("manifest_identity_mismatch")
        else:
            timestamp = _iso(self.clock())
            stages = {
                stage: StageRecord(stage, "pending", 0, None, None, None, (), {}, None)
                for stage in STAGE_ORDER
            }
            self.save(
                RunManifest(
                    version="1.0",
                    run_id=run_id,
                    fixture_only=fixture_only,
                    network_requests_made=0,
                    status="pending",
                    stages=stages,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )

    def load(self) -> RunManifest:
        raw = json.loads(self.path.read_text("utf-8"))
        raw_stages = raw["stages"]
        if set(raw_stages) != set(STAGE_ORDER):
            raise ValueError("manifest_stage_contract_invalid")
        stages = {
            name: StageRecord(
                name=name,
                status=str(raw_stages[name]["status"]),
                attempts=int(raw_stages[name]["attempts"]),
                started_at=raw_stages[name].get("started_at"),
                ended_at=raw_stages[name].get("ended_at"),
                input_hash=raw_stages[name].get("input_hash"),
                output_refs=tuple(
                    str(value) for value in raw_stages[name].get("output_refs", ())
                ),
                output_metadata=dict(raw_stages[name].get("output_metadata", {})),
                error_code=raw_stages[name].get("error_code"),
            )
            for name in STAGE_ORDER
        }
        return RunManifest(
            version=str(raw["version"]),
            run_id=str(raw["run_id"]),
            fixture_only=bool(raw["fixture_only"]),
            network_requests_made=int(raw["network_requests_made"]),
            status=str(raw["status"]),
            stages=stages,
            created_at=str(raw["created_at"]),
            updated_at=str(raw["updated_at"]),
        )

    def save(self, manifest: RunManifest) -> None:
        _atomic_write(self.path, manifest_to_dict(manifest))


def _manifest_status(stages: Mapping[str, StageRecord]) -> str:
    statuses = {item.status for item in stages.values()}
    if "failed" in statuses:
        return "failed"
    if all(item.status == "completed" for item in stages.values()):
        return "completed"
    if "running" in statuses or "completed" in statuses:
        return "in_progress"
    return "pending"


def run_stage(
    store: RunManifestStore,
    stage: str,
    inputs: object,
    operation: Callable[[], StageOutput],
) -> StageExecutionResult:
    if stage not in STAGE_ORDER:
        raise StageExecutionError("stage_invalid")
    manifest = store.load()
    index = STAGE_ORDER.index(stage)
    if any(
        manifest.stages[upstream].status != "completed"
        for upstream in STAGE_ORDER[:index]
    ):
        raise StageExecutionError("upstream_stage_incomplete")
    digest = _input_hash(inputs)
    current = manifest.stages[stage]
    if current.status == "completed":
        if current.input_hash != digest:
            raise StageExecutionError("completed_stage_input_changed")
        return StageExecutionResult(
            stage=stage,
            reused=True,
            output_refs=current.output_refs,
            output_metadata=current.output_metadata,
        )

    started_at = _iso(store.clock())
    running = replace(
        current,
        status="running",
        attempts=current.attempts + 1,
        started_at=started_at,
        ended_at=None,
        input_hash=digest,
        output_refs=(),
        output_metadata={},
        error_code=None,
    )
    stages = dict(manifest.stages)
    stages[stage] = running
    store.save(
        replace(
            manifest,
            status=_manifest_status(stages),
            stages=stages,
            updated_at=started_at,
        )
    )
    try:
        output = operation()
        if not isinstance(output, StageOutput):
            raise TypeError("stage_operation_must_return_stage_output")
        metadata = _safe_metadata(output.metadata)
        refs = tuple(str(item) for item in output.output_refs)
    except Exception as exc:
        ended_at = _iso(store.clock())
        error_code = f"{stage}_failed:{type(exc).__name__}"
        latest = store.load()
        failed_stages = dict(latest.stages)
        failed_stages[stage] = replace(
            latest.stages[stage],
            status="failed",
            ended_at=ended_at,
            output_refs=(),
            output_metadata={},
            error_code=error_code,
        )
        store.save(
            replace(
                latest,
                status="failed",
                stages=failed_stages,
                updated_at=ended_at,
            )
        )
        raise StageExecutionError(error_code) from exc

    ended_at = _iso(store.clock())
    latest = store.load()
    completed_stages = dict(latest.stages)
    completed_stages[stage] = replace(
        latest.stages[stage],
        status="completed",
        ended_at=ended_at,
        output_refs=refs,
        output_metadata=metadata,
        error_code=None,
    )
    updated = replace(
        latest,
        status=_manifest_status(completed_stages),
        stages=completed_stages,
        updated_at=ended_at,
    )
    store.save(updated)
    return StageExecutionResult(stage, False, refs, metadata)


def run_collection_stage(
    store: RunManifestStore,
    inputs: object,
    operation: Callable[[], StageOutput],
) -> StageExecutionResult:
    return run_stage(store, "collect", inputs, operation)


def run_analysis_stage(
    store: RunManifestStore,
    inputs: object,
    operation: Callable[[], StageOutput],
) -> StageExecutionResult:
    return run_stage(store, "analyze", inputs, operation)


def run_brief_stage(
    store: RunManifestStore,
    inputs: object,
    operation: Callable[[], StageOutput],
) -> StageExecutionResult:
    return run_stage(store, "brief", inputs, operation)
