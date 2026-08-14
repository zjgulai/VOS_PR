"""加载并校验 PR 核心媒体 P0 的冻结范围。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .contracts import ContractViolation, normalize_id_part


@dataclass(frozen=True)
class OutletScope:
    canonical_name: str
    edition_status: str


@dataclass(frozen=True)
class SourceWorkbookRef:
    path: str
    sheet: str
    approval_status: str


@dataclass(frozen=True)
class DictionaryRef:
    path: str
    version: str
    approval_status: str


@dataclass(frozen=True)
class P0Scope:
    version: str
    scope_id: str
    scope_version: str
    status: str
    markets: tuple[str, ...]
    languages: tuple[str, ...]
    category: str
    incremental_days: int
    baseline_days: int
    expected_outlets: int
    expected_candidate_journalists: int
    outlets: tuple[OutletScope, ...]
    source_workbook: SourceWorkbookRef
    dictionary: DictionaryRef
    gate0_ref: str


def _violation(code: str, field: str, message: str) -> ContractViolation:
    return ContractViolation(code=code, field=field, message=message)


def _as_list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def validate_scope_dict(data: Mapping[str, object]) -> list[ContractViolation]:
    """Validate raw JSON while retaining every independent contract violation."""
    violations: list[ContractViolation] = []

    markets = _as_list(data.get("markets"))
    if markets != ["US"]:
        violations.append(
            _violation(
                "p0_market_out_of_scope",
                "markets",
                "P0 markets must be exactly ['US']",
            )
        )

    languages = _as_list(data.get("languages"))
    if languages != ["en"]:
        violations.append(
            _violation(
                "p0_language_out_of_scope",
                "languages",
                "P0 languages must be exactly ['en']",
            )
        )

    if data.get("category") != "pumping":
        violations.append(
            _violation(
                "p0_category_out_of_scope",
                "category",
                "P0 category must be pumping",
            )
        )

    if data.get("incremental_days") != 30:
        violations.append(
            _violation(
                "incremental_window_must_be_30",
                "incremental_days",
                "P0 incremental window must be 30 days",
            )
        )

    baseline_days = data.get("baseline_days")
    if not isinstance(baseline_days, int) or isinstance(baseline_days, bool):
        violations.append(
            _violation(
                "baseline_window_invalid",
                "baseline_days",
                "baseline_days must be an integer",
            )
        )
    elif baseline_days < 1 or baseline_days > 180:
        violations.append(
            _violation(
                "baseline_window_exceeded",
                "baseline_days",
                "P0 baseline must be between 1 and 180 days",
            )
        )

    expected_outlets = data.get("expected_outlets")
    if expected_outlets != 11:
        violations.append(
            _violation(
                "expected_outlet_count_must_be_11",
                "expected_outlets",
                "P0 expected_outlets must be 11",
            )
        )

    expected_journalists = data.get("expected_candidate_journalists")
    if expected_journalists != 48:
        violations.append(
            _violation(
                "expected_journalist_count_must_be_48",
                "expected_candidate_journalists",
                "P0 expected_candidate_journalists must be 48",
            )
        )

    outlets = _as_list(data.get("outlets"))
    if not isinstance(expected_outlets, bool) and isinstance(expected_outlets, int):
        if len(outlets) != expected_outlets:
            violations.append(
                _violation(
                    "outlet_count_mismatch",
                    "outlets",
                    "outlet rows must equal expected_outlets",
                )
            )

    outlet_names: list[str] = []
    for index, outlet in enumerate(outlets):
        if not isinstance(outlet, Mapping):
            violations.append(
                _violation(
                    "outlet_record_invalid",
                    f"outlets.{index}",
                    "each outlet must be an object",
                )
            )
            continue
        name = outlet.get("canonical_name")
        if not isinstance(name, str) or not name.strip():
            violations.append(
                _violation(
                    "outlet_name_missing",
                    f"outlets.{index}.canonical_name",
                    "canonical_name must be non-empty",
                )
            )
        else:
            outlet_names.append(normalize_id_part(name))
        if outlet.get("edition_status") not in {"pending", "verified", "blocked"}:
            violations.append(
                _violation(
                    "edition_status_invalid",
                    f"outlets.{index}.edition_status",
                    "edition_status must be pending, verified, or blocked",
                )
            )
    if len(outlet_names) != len(set(outlet_names)):
        violations.append(
            _violation(
                "duplicate_outlet",
                "outlets",
                "outlet canonical names must be unique after normalization",
            )
        )

    for field in ("version", "scope_id", "scope_version", "status", "gate0_ref"):
        if not isinstance(data.get(field), str) or not str(data[field]).strip():
            violations.append(
                _violation(
                    "required_string_missing",
                    field,
                    f"{field} must be a non-empty string",
                )
            )

    source_workbook = data.get("source_workbook")
    if not isinstance(source_workbook, Mapping) or any(
        not isinstance(source_workbook.get(field), str)
        or not str(source_workbook[field]).strip()
        for field in ("path", "sheet", "approval_status")
    ):
        violations.append(
            _violation(
                "source_workbook_ref_invalid",
                "source_workbook",
                "source_workbook requires path, sheet, and approval_status",
            )
        )

    dictionary = data.get("dictionary")
    if not isinstance(dictionary, Mapping) or any(
        not isinstance(dictionary.get(field), str)
        or not str(dictionary[field]).strip()
        for field in ("path", "version", "approval_status")
    ):
        violations.append(
            _violation(
                "dictionary_ref_invalid",
                "dictionary",
                "dictionary requires path, version, and approval_status",
            )
        )

    return violations


def _parse_scope(data: Mapping[str, object]) -> P0Scope:
    source = data["source_workbook"]
    dictionary = data["dictionary"]
    assert isinstance(source, Mapping)
    assert isinstance(dictionary, Mapping)
    raw_outlets = data["outlets"]
    assert isinstance(raw_outlets, list)
    return P0Scope(
        version=str(data["version"]),
        scope_id=str(data["scope_id"]),
        scope_version=str(data["scope_version"]),
        status=str(data["status"]),
        markets=tuple(str(value) for value in data["markets"]),
        languages=tuple(str(value) for value in data["languages"]),
        category=str(data["category"]),
        incremental_days=int(data["incremental_days"]),
        baseline_days=int(data["baseline_days"]),
        expected_outlets=int(data["expected_outlets"]),
        expected_candidate_journalists=int(data["expected_candidate_journalists"]),
        outlets=tuple(
            OutletScope(
                canonical_name=str(item["canonical_name"]),
                edition_status=str(item["edition_status"]),
            )
            for item in raw_outlets
        ),
        source_workbook=SourceWorkbookRef(
            path=str(source["path"]),
            sheet=str(source["sheet"]),
            approval_status=str(source["approval_status"]),
        ),
        dictionary=DictionaryRef(
            path=str(dictionary["path"]),
            version=str(dictionary["version"]),
            approval_status=str(dictionary["approval_status"]),
        ),
        gate0_ref=str(data["gate0_ref"]),
    )


def validate_scope(scope: P0Scope) -> list[ContractViolation]:
    """Validate a parsed scope using the same public contract."""
    return validate_scope_dict(
        {
            "version": scope.version,
            "scope_id": scope.scope_id,
            "scope_version": scope.scope_version,
            "status": scope.status,
            "markets": list(scope.markets),
            "languages": list(scope.languages),
            "category": scope.category,
            "incremental_days": scope.incremental_days,
            "baseline_days": scope.baseline_days,
            "expected_outlets": scope.expected_outlets,
            "expected_candidate_journalists": scope.expected_candidate_journalists,
            "outlets": [
                {
                    "canonical_name": item.canonical_name,
                    "edition_status": item.edition_status,
                }
                for item in scope.outlets
            ],
            "source_workbook": {
                "path": scope.source_workbook.path,
                "sheet": scope.source_workbook.sheet,
                "approval_status": scope.source_workbook.approval_status,
            },
            "dictionary": {
                "path": scope.dictionary.path,
                "version": scope.dictionary.version,
                "approval_status": scope.dictionary.approval_status,
            },
            "gate0_ref": scope.gate0_ref,
        }
    )


def load_scope(path: Path) -> P0Scope:
    """Load a scope file or fail with every observed contract violation."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"scope_read_failed: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("scope_root_invalid: JSON root must be an object")
    violations = validate_scope_dict(raw)
    if violations:
        detail = "; ".join(f"{item.code}: {item.message}" for item in violations)
        raise ValueError(detail)
    return _parse_scope(raw)
