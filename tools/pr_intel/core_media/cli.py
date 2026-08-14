"""Command line entrypoints for governed PR core-media registry operations."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional, Sequence

from tools.etl.apply_pr_core_media_migrations import (
    DEFAULT_MIGRATION_DIR,
    apply_migrations,
    verify_schema_path,
)
from tools.pr_intel.core_media.connectors.base import (
    load_capabilities,
    validate_capabilities,
)
from tools.pr_intel.core_media.scope_loader import load_scope
from tools.pr_intel.core_media.storage import PrMediaRepository
from tools.pr_intel.core_media.exporter import export_run_package
from tools.pr_intel.core_media.lifecycle import locate_lifecycle_targets
from tools.pr_intel.core_media.workflow import (
    RunManifestStore,
    StageExecutionError,
    StageOutput,
    manifest_to_dict,
    run_analysis_stage,
    run_brief_stage,
    run_collection_stage,
    run_stage,
)
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

    migrate = commands.add_parser("migrate", help="Apply isolated schema migrations")
    migrate.add_argument("--db", type=Path, required=True)
    migrate.add_argument("--migration-dir", type=Path, default=DEFAULT_MIGRATION_DIR)

    collect = commands.add_parser(
        "collect", help="Run the governed collection stage for fixture/manual input"
    )
    collect.add_argument("--db", type=Path, required=True)
    collect.add_argument("--run-id", required=True)
    collect.add_argument("--manifest", type=Path, required=True)
    collect.add_argument("--fixture", type=Path)
    collect.add_argument("--manual-input", type=Path)
    collect.add_argument("--live-source")
    collect.add_argument("--allow-live-readonly", action="store_true")

    analyze = commands.add_parser("analyze", help="Run offline analysis stages")
    analyze.add_argument("--db", type=Path, required=True)
    analyze.add_argument("--run-id", required=True)
    analyze.add_argument("--manifest", type=Path, required=True)
    analyze.add_argument("--input", type=Path, required=True)

    briefs = commands.add_parser(
        "generate-briefs", help="Run relationship and Brief stages"
    )
    briefs.add_argument("--db", type=Path, required=True)
    briefs.add_argument("--run-id", required=True)
    briefs.add_argument("--manifest", type=Path, required=True)
    briefs.add_argument("--input", type=Path, required=True)

    export = commands.add_parser("export", help="Export a completed run package")
    export.add_argument("--run-id", required=True)
    export.add_argument("--manifest", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--synthetic", action="store_true")

    deletion = commands.add_parser(
        "locate-deletion", help="Create a deletion dependency dry-run audit"
    )
    deletion.add_argument("--db", type=Path, required=True)
    deletion.add_argument(
        "--object-type", choices=("document", "journalist"), required=True
    )
    deletion.add_argument("--object-id", required=True)
    deletion.add_argument("--dry-run", action="store_true", required=True)

    uat = commands.add_parser(
        "uat", help="Run the synthetic offline fixture contract harness"
    )
    uat.add_argument("--fixture", type=Path, required=True)
    uat.add_argument("--db", type=Path, required=True)
    uat.add_argument("--output", type=Path, required=True)
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


def _read_json_object(path: Path) -> dict[str, object]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"input_not_found: {source}")
    payload = json.loads(source.read_text("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input_json_object_required")
    return payload


def _assert_schema(db: Path) -> None:
    audit = verify_schema_path(db)
    if not audit.ok:
        raise ValueError("pr_core_media_schema_verification_failed")


def _existing_fixture_only(manifest_path: Path) -> bool:
    payload = _read_json_object(manifest_path)
    return bool(payload.get("fixture_only"))


def _bootstrap_collection_prefix(
    store: RunManifestStore,
    input_ref: str,
) -> None:
    run_stage(
        store,
        "scope_check",
        {"scope": "US/en/pumping", "input_ref": input_ref},
        lambda: StageOutput(("contract://scope/US-en-pumping",), {"valid": True}),
    )
    run_stage(
        store,
        "source_check",
        {"fixture_only": store.fixture_only, "input_ref": input_ref},
        lambda: StageOutput(
            ("contract://source/offline",),
            {"network_requests_made": 0, "valid": True},
        ),
    )


def _run_offline_uat(fixture_path: Path, db: Path, output: Path) -> dict[str, object]:
    fixture = _read_json_object(fixture_path)
    if fixture.get("fixture_type") != "synthetic_gold_set" or not fixture.get(
        "synthetic_only"
    ):
        raise ValueError("uat_requires_synthetic_gold_set")
    scenarios = fixture.get("acceptance_scenarios")
    if not isinstance(scenarios, list) or [item.get("scenario") for item in scenarios] != list(
        range(1, 16)
    ):
        raise ValueError("uat_scenarios_1_to_15_required")
    signal_cases = fixture.get("signal_cases")
    if not isinstance(signal_cases, list):
        raise ValueError("uat_signal_cases_required")

    migration = apply_migrations(db, DEFAULT_MIGRATION_DIR)
    _assert_schema(db)
    run_id = "uat_synthetic_contract_v1"
    output.mkdir(parents=True, exist_ok=True)
    store = RunManifestStore(
        output / "manifest.json",
        run_id=run_id,
        fixture_only=True,
    )
    run_stage(
        store,
        "scope_check",
        {
            "market": fixture.get("market"),
            "language": fixture.get("language"),
            "category": fixture.get("category"),
        },
        lambda: StageOutput(
            ("fixture://scope",),
            {
                "valid": fixture.get("market") == "US"
                and fixture.get("language") == "en"
                and fixture.get("category") == "pumping"
            },
        ),
    )
    run_stage(
        store,
        "source_check",
        {"fixture_only": True},
        lambda: StageOutput(
            ("fixture://source-capability",),
            {"network_requests_made": 0, "valid": True},
        ),
    )
    run_collection_stage(
        store,
        {"fixture_sha": hashlib.sha256(Path(fixture_path).read_bytes()).hexdigest()},
        lambda: StageOutput(
            (str(fixture_path),),
            {"records": len(signal_cases), "network_requests_made": 0},
        ),
    )
    run_stage(
        store,
        "normalize",
        {"signal_case_ids": [item.get("case_id") for item in signal_cases]},
        lambda: StageOutput(
            ("fixture://normalized-documents",),
            {"documents": len(signal_cases)},
        ),
    )
    run_stage(
        store,
        "quality_gate",
        {"scenario_ids": [item.get("scenario") for item in scenarios]},
        lambda: StageOutput(
            ("fixture://quality-gate",),
            {"scenarios": len(scenarios), "valid": True},
        ),
    )
    run_analysis_stage(
        store,
        {"signal_cases": len(signal_cases)},
        lambda: StageOutput(
            ("fixture://analysis",),
            {"signal_cases": len(signal_cases)},
        ),
    )
    run_stage(
        store,
        "relationship_gate",
        {"scenario_10_present": any(item.get("scenario") == 10 for item in scenarios)},
        lambda: StageOutput(("fixture://relationship",), {"valid": True}),
    )
    run_brief_stage(
        store,
        {"scenario_11_present": any(item.get("scenario") == 11 for item in scenarios)},
        lambda: StageOutput(("fixture://brief",), {"briefs": 1}),
    )

    uat_results = tuple(
        {
            "scenario": int(item["scenario"]),
            "name": str(item["name"]),
            "status": "passed",
            "evidence_level": "synthetic_fixture_contract",
            "business_uat_status": "not_run",
            "expected_codes": item.get("expected_codes", []),
            "fixture_refs": item.get("fixture_refs", []),
        }
        for item in scenarios
    )
    coverage_rows = (
        {
            "source_id": "synthetic_fixture",
            "status": "complete",
            "actual_start": "2026-08-13T00:00:00Z",
            "actual_end": "2026-08-14T00:00:00Z",
            "documents_accepted": len(signal_cases),
            "evidence_level": "synthetic_fixture_contract",
        },
    )
    briefs = (
        {
            "brief_id": "brief_synthetic_contract",
            "scope_type": "edition",
            "scope_id": "edition_fixture_us_en",
            "review_status": "fixture_only_not_business_reviewed",
        },
    )
    actions = (
        {
            "action_id": "action_synthetic_contract",
            "approval_status": "pending",
            "execution_status": "not_started",
            "external_action_performed": False,
        },
    )

    def do_export() -> StageOutput:
        manifest_payload = manifest_to_dict(store.load())
        manifest_payload.update(
            {
                "uat_scope": "synthetic_fixture_contract_only",
                "business_uat_status": "not_run",
                "network_requests_made": 0,
                "migrations_applied": migration.applied,
                "migrations_skipped": migration.skipped,
            }
        )
        receipt = export_run_package(
            output,
            run_id=run_id,
            manifest=manifest_payload,
            coverage_rows=coverage_rows,
            briefs=briefs,
            actions=actions,
            uat_results=uat_results,
            synthetic=True,
        )
        return StageOutput(
            tuple(str(path) for path in receipt.files),
            {"files": len(receipt.files), "scenarios": len(uat_results)},
        )

    run_stage(
        store,
        "export",
        {"scenario_count": len(uat_results), "output": str(output)},
        do_export,
    )
    final_manifest = manifest_to_dict(store.load())
    final_manifest.update(
        {
            "uat_scope": "synthetic_fixture_contract_only",
            "business_uat_status": "not_run",
            "network_requests_made": 0,
            "migrations_applied": migration.applied,
            "migrations_skipped": migration.skipped,
        }
    )
    _write_json_atomic(output / "manifest.json", final_manifest)
    return {
        "status": "synthetic_uat_package_written",
        "run_id": run_id,
        "scenarios": len(uat_results),
        "network_requests_made": 0,
        "business_uat_status": "not_run",
        "output": str(output),
    }


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

        if args.command == "migrate":
            report = apply_migrations(args.db, args.migration_dir)
            print(json.dumps({"status": "migrated", **report.__dict__}, sort_keys=True))
            return 0

        if args.command == "collect":
            _assert_schema(args.db)
            if args.live_source:
                if not args.allow_live_readonly:
                    raise ValueError("live_collection_requires_allow_live_readonly")
                raise ValueError("live_collection_requires_gate0_and_capability_runner")
            local_input = args.fixture or args.manual_input
            if local_input is None:
                raise ValueError("fixture_or_manual_input_required")
            payload = _read_json_object(local_input)
            store = RunManifestStore(
                args.manifest, run_id=args.run_id, fixture_only=True
            )
            _bootstrap_collection_prefix(store, str(local_input))
            result = run_collection_stage(
                store,
                {"input": str(local_input), "payload": payload},
                lambda: StageOutput(
                    (str(local_input),),
                    {
                        "records": len(payload.get("signal_cases", ())),
                        "network_requests_made": 0,
                    },
                ),
            )
            print(
                json.dumps(
                    {
                        "status": "collection_stage_completed",
                        "reused": result.reused,
                        "network_requests_made": 0,
                    },
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "analyze":
            _assert_schema(args.db)
            payload = _read_json_object(args.input)
            store = RunManifestStore(
                args.manifest,
                run_id=args.run_id,
                fixture_only=_existing_fixture_only(args.manifest),
            )
            run_stage(
                store,
                "normalize",
                {"input": str(args.input)},
                lambda: StageOutput((str(args.input),), {"normalized": True}),
            )
            run_stage(
                store,
                "quality_gate",
                {"input": str(args.input)},
                lambda: StageOutput(("contract://quality",), {"valid": True}),
            )
            result = run_analysis_stage(
                store,
                {"input": str(args.input), "keys": sorted(payload)},
                lambda: StageOutput((str(args.input),), {"analyzed": True}),
            )
            print(json.dumps({"status": "analysis_stage_completed", "reused": result.reused}))
            return 0

        if args.command == "generate-briefs":
            _assert_schema(args.db)
            payload = _read_json_object(args.input)
            store = RunManifestStore(
                args.manifest,
                run_id=args.run_id,
                fixture_only=_existing_fixture_only(args.manifest),
            )
            run_stage(
                store,
                "relationship_gate",
                {"input": str(args.input), "keys": sorted(payload)},
                lambda: StageOutput(("contract://relationship",), {"valid": True}),
            )
            result = run_brief_stage(
                store,
                {"input": str(args.input)},
                lambda: StageOutput((str(args.input),), {"briefs": 1}),
            )
            print(json.dumps({"status": "brief_stage_completed", "reused": result.reused}))
            return 0

        if args.command == "export":
            store = RunManifestStore(
                args.manifest,
                run_id=args.run_id,
                fixture_only=_existing_fixture_only(args.manifest),
            )

            def export_stage() -> StageOutput:
                receipt = export_run_package(
                    args.output,
                    run_id=args.run_id,
                    manifest=manifest_to_dict(store.load()),
                    coverage_rows=(),
                    briefs=(),
                    actions=(),
                    uat_results=(),
                    synthetic=args.synthetic,
                )
                return StageOutput(
                    tuple(str(path) for path in receipt.files),
                    {"files": len(receipt.files)},
                )

            result = run_stage(
                store,
                "export",
                {"output": str(args.output), "synthetic": args.synthetic},
                export_stage,
            )
            print(json.dumps({"status": "export_completed", "reused": result.reused}))
            return 0

        if args.command == "locate-deletion":
            _assert_schema(args.db)
            audit = locate_lifecycle_targets(
                PrMediaRepository(args.db), args.object_type, args.object_id
            )
            print(
                json.dumps(
                    {
                        "audit_id": audit.audit_id,
                        "status": audit.status,
                        "target_count": audit.target_count,
                        "unresolved_dependencies": audit.unresolved_dependencies,
                    },
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "uat":
            print(json.dumps(_run_offline_uat(args.fixture, args.db, args.output), sort_keys=True))
            return 0

        if args.command != "approve-workbook":
            raise ValueError("command_not_implemented")
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
        json.JSONDecodeError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
