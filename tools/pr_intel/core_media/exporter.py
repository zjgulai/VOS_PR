"""Atomic JSON, Markdown and CSV exports for a core-media run package."""
from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = PROJECT_ROOT / "reports/pr_intel/core_media/runtime"
_RUN_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{2,127}$")


@dataclass(frozen=True)
class ExportReceipt:
    run_id: str
    output_dir: str
    files: tuple[Path, ...]


def _serializable(value: object) -> object:
    if is_dataclass(value):
        return {key: _serializable(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp = Path(handle.name)
    try:
        with handle:
            handle.write(text)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _json_text(value: object) -> str:
    return json.dumps(
        _serializable(value), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"


def _csv_safe(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        text = json.dumps(_serializable(value), ensure_ascii=False, sort_keys=True)
    else:
        text = str(_serializable(value))
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _csv_text(rows: Sequence[Mapping[str, object]]) -> str:
    columns = sorted({str(key) for row in rows for key in row})
    stream = StringIO(newline="")
    if columns:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _csv_safe(row.get(column)) for column in columns})
    return stream.getvalue()


def _markdown(title: str, rows: Sequence[Mapping[str, object]]) -> str:
    lines = [f"# {title}", ""]
    if not rows:
        lines.extend(["No records.", ""])
        return "\n".join(lines)
    for index, row in enumerate(rows, start=1):
        identifier = row.get("brief_id") or row.get("scenario") or index
        lines.extend([f"## {identifier}", ""])
        for key in sorted(row):
            lines.append(f"- {key}: {json.dumps(_serializable(row[key]), ensure_ascii=False)}")
        lines.append("")
    return "\n".join(lines)


def export_run_package(
    output_dir: Path,
    *,
    run_id: str,
    manifest: Mapping[str, object],
    coverage_rows: Sequence[Mapping[str, object]],
    briefs: Sequence[Mapping[str, object]],
    actions: Sequence[Mapping[str, object]],
    uat_results: Sequence[Mapping[str, object]],
    synthetic: bool,
) -> ExportReceipt:
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id_invalid")
    output = Path(output_dir)
    if output.is_symlink():
        raise ValueError("export_output_symlink_not_allowed")
    if not synthetic:
        expected = (RUNTIME_ROOT / run_id).resolve()
        if output.resolve() != expected:
            raise ValueError("live_export_must_use_runtime_directory")
    output.mkdir(parents=True, exist_ok=True)

    normalized_briefs = tuple(dict(_serializable(item)) for item in briefs)
    normalized_actions = tuple(dict(_serializable(item)) for item in actions)
    normalized_uat = tuple(dict(_serializable(item)) for item in uat_results)
    files = {
        "manifest.json": _json_text(manifest),
        "coverage.csv": _csv_text(coverage_rows),
        "briefs.json": _json_text(normalized_briefs),
        "briefs.md": _markdown("PR Core Media Briefs", normalized_briefs),
        "actions.csv": _csv_text(normalized_actions),
        "uat-results.json": _json_text(normalized_uat),
        "uat-results.md": _markdown("PR Core Media UAT Results", normalized_uat),
    }
    written: list[Path] = []
    for name, contents in files.items():
        path = output / name
        _atomic_text(path, contents)
        written.append(path)
    return ExportReceipt(run_id, str(output), tuple(sorted(written)))
