"""Command line entrypoints for governed PR core-media registry operations."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional, Sequence

from tools.etl.apply_pr_core_media_migrations import verify_schema_path
from tools.pr_intel.core_media.connectors.base import (
    load_capabilities,
    validate_capabilities,
)
from tools.pr_intel.core_media.scope_loader import load_scope
from tools.pr_intel.core_media.storage import PrMediaRepository
from tools.pr_intel.core_media.workbook_importer import (
    ImportApprovalError,
    WorkbookImportError,
    approve_workbook_import,
    preview_workbook,
)


_APPROVED_FRONTMATTER_RE = re.compile(
    r"(?m)^status:\s*approved\s*$", re.IGNORECASE
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pr-core-media")
    commands = parser.add_subparsers(dest="command", required=True)

    preview = commands.add_parser(
        "preview-workbook", help="Parse a workbook and write audit JSON without database writes"
    )
    preview.add_argument("--input", type=Path, required=True)
    preview.add_argument("--sheet", required=True)
    preview.add_argument("--import-version", required=True)
    preview.add_argument("--output", type=Path, required=True)

    approve = commands.add_parser(
        "approve-workbook", help="Approve a previewed workbook into an existing isolated schema"
    )
    approve.add_argument("--input", type=Path, required=True)
    approve.add_argument("--sheet", required=True)
    approve.add_argument("--import-version", required=True)
    approve.add_argument("--db", type=Path, required=True)
    approve.add_argument("--approved-by-role", required=True)
    approve.add_argument("--gate0-decision-ref", type=Path, required=True)
    approve.add_argument(
        "--confirm-registry-write",
        action="store_true",
        required=True,
        help="Required acknowledgement that this command writes a new registry version",
    )

    validate = commands.add_parser(
        "validate-sources",
        help="Validate source capability coverage and rights without network requests",
    )
    validate.add_argument("--scope", type=Path, required=True)
    validate.add_argument("--capabilities", type=Path, required=True)
    validate.add_argument(
        "--offline",
        action="store_true",
        required=True,
        help="Required safety boundary; this command never performs network requests",
    )
    return parser


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_path, output)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _assert_gate0_approved(path: Path) -> None:
    decision_ref = Path(path)
    if not decision_ref.is_file():
        raise ImportApprovalError("gate0_decision_ref_not_found")
    text = decision_ref.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)
    if len(frontmatter) < 3 or not _APPROVED_FRONTMATTER_RE.search(frontmatter[1]):
        raise ImportApprovalError("gate0_business_signoff_not_approved")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate-sources":
            scope = load_scope(args.scope)
            capabilities = load_capabilities(args.capabilities)
            audit = validate_capabilities(scope, capabilities, offline=True)
            print(
                json.dumps(
                    audit.to_dict(),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "preview-workbook":
            batch = preview_workbook(args.input, args.sheet, args.import_version)
            _write_json_atomic(args.output, batch.to_preview_dict())
            print(
                json.dumps(
                    {
                        "status": "preview_written",
                        "output": str(args.output),
                        "outlets": len(batch.outlets),
                        "journalists": len(batch.journalists),
                        "review_items": len(batch.review_items),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0

        _assert_gate0_approved(args.gate0_decision_ref)
        audit = verify_schema_path(args.db)
        if not audit.ok:
            raise ImportApprovalError("pr_core_media_schema_verification_failed")
        batch = preview_workbook(args.input, args.sheet, args.import_version)
        report = approve_workbook_import(
            PrMediaRepository(args.db), batch, args.approved_by_role
        )
        print(
            json.dumps(
                {
                    "status": report.status,
                    "import_version": report.import_version,
                    "outlets": report.outlet_count,
                    "journalists": report.journalist_count,
                    "touchpoints": report.touchpoint_count,
                    "errors": [
                        {"code": item.code, "message": item.message}
                        for item in report.errors
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0 if report.status == "approved" else 1
    except (
        WorkbookImportError,
        ImportApprovalError,
        FileNotFoundError,
        ValueError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
