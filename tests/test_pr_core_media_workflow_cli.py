from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.pr_intel.core_media.cli import main
from tools.pr_intel.core_media.exporter import export_run_package
from tools.pr_intel.core_media.workflow import (
    RunManifestStore,
    StageExecutionError,
    StageOutput,
    run_collection_stage,
    run_stage,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pr_core_media/uat_expected.json"


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 14, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        result = self.value
        self.value += timedelta(seconds=1)
        return result


class WorkflowTests(unittest.TestCase):
    def test_completed_stage_is_reused_without_repeating_side_effect(self) -> None:
        with TemporaryDirectory() as directory:
            store = RunManifestStore(
                Path(directory) / "manifest.json",
                run_id="run_fixture_resume",
                fixture_only=True,
                clock=Clock(),
            )
            calls = []
            run_stage(
                store,
                "scope_check",
                {"scope": "fixture"},
                lambda: StageOutput(("fixture://scope",), {"ok": True}),
            )
            run_stage(
                store,
                "source_check",
                {"sources": "fixture"},
                lambda: StageOutput(("fixture://sources",), {"ok": True}),
            )

            def operation() -> StageOutput:
                calls.append("called")
                return StageOutput(("fixture://collected",), {"records": 2})

            first = run_collection_stage(
                store, {"fixture": "records-v1"}, operation
            )
            resumed = run_collection_stage(
                store, {"fixture": "records-v1"}, operation
            )

            self.assertFalse(first.reused)
            self.assertTrue(resumed.reused)
            self.assertEqual(["called"], calls)
            manifest = store.load()
            self.assertEqual("completed", manifest.stages["collect"].status)
            self.assertEqual(1, manifest.stages["collect"].attempts)

    def test_failure_stops_downstream_and_same_stage_can_resume(self) -> None:
        with TemporaryDirectory() as directory:
            store = RunManifestStore(
                Path(directory) / "manifest.json",
                run_id="run_fixture_failure",
                fixture_only=True,
                clock=Clock(),
            )
            run_stage(
                store,
                "scope_check",
                {"scope": "fixture"},
                lambda: StageOutput((), {"ok": True}),
            )

            def fail() -> StageOutput:
                raise ValueError("sensitive payload must not enter manifest")

            with self.assertRaisesRegex(StageExecutionError, "source_check_failed"):
                run_stage(store, "source_check", {"sources": "v1"}, fail)
            with self.assertRaisesRegex(StageExecutionError, "upstream_stage_incomplete"):
                run_collection_stage(
                    store,
                    {"fixture": "v1"},
                    lambda: StageOutput((), {"records": 0}),
                )
            result = run_stage(
                store,
                "source_check",
                {"sources": "v1"},
                lambda: StageOutput(("fixture://recovered",), {"ok": True}),
            )
            self.assertFalse(result.reused)
            manifest_text = (Path(directory) / "manifest.json").read_text("utf-8")
            self.assertNotIn("sensitive payload", manifest_text)
            self.assertEqual(2, store.load().stages["source_check"].attempts)

    def test_completed_stage_rejects_changed_inputs_under_same_run_id(self) -> None:
        with TemporaryDirectory() as directory:
            store = RunManifestStore(
                Path(directory) / "manifest.json",
                run_id="run_fixture_drift",
                fixture_only=True,
                clock=Clock(),
            )
            run_stage(
                store,
                "scope_check",
                {"scope": "v1"},
                lambda: StageOutput((), {"ok": True}),
            )
            with self.assertRaisesRegex(StageExecutionError, "completed_stage_input_changed"):
                run_stage(
                    store,
                    "scope_check",
                    {"scope": "v2"},
                    lambda: StageOutput((), {"ok": True}),
                )


class ExportAndCliTests(unittest.TestCase):
    def test_export_writes_json_markdown_csv_and_escapes_csv_formula(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "run_fixture_export"
            manifest = {
                "run_id": "run_fixture_export",
                "fixture_only": True,
                "network_requests_made": 0,
            }
            receipt = export_run_package(
                output,
                run_id="run_fixture_export",
                manifest=manifest,
                coverage_rows=(
                    {
                        "source_id": "source_fixture",
                        "status": "complete",
                        "gap_reason": "=HYPERLINK(\"bad\")",
                    },
                ),
                briefs=({"brief_id": "brief_fixture", "scope_type": "edition"},),
                actions=({"action_id": "action_fixture", "approval_status": "pending"},),
                uat_results=({"scenario": 1, "status": "passed"},),
                synthetic=True,
            )
            self.assertEqual(
                {
                    "actions.csv",
                    "briefs.json",
                    "briefs.md",
                    "coverage.csv",
                    "manifest.json",
                    "uat-results.json",
                    "uat-results.md",
                },
                {path.name for path in receipt.files},
            )
            self.assertIn("'=HYPERLINK", (output / "coverage.csv").read_text("utf-8"))

    def test_write_commands_require_explicit_db_argument(self) -> None:
        for command in ("migrate", "collect", "analyze", "generate-briefs"):
            with self.subTest(command=command), self.assertRaises(SystemExit) as error:
                main([command])
            self.assertEqual(2, error.exception.code)

    def test_collect_without_live_flag_rejects_live_mode_before_network(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "fixture.duckdb"
            self.assertEqual(0, main(["migrate", "--db", str(db)]))
            code = main(
                [
                    "collect",
                    "--db",
                    str(db),
                    "--run-id",
                    "run_live_blocked",
                    "--manifest",
                    str(Path(directory) / "manifest.json"),
                    "--live-source",
                    "source_fixture",
                ]
            )
            self.assertEqual(2, code)

    def test_uat_cli_generates_15_scenario_report_without_network(self) -> None:
        with TemporaryDirectory() as directory:
            db = Path(directory) / "uat.duckdb"
            output = Path(directory) / "uat-output"
            code = main(
                [
                    "uat",
                    "--fixture",
                    str(FIXTURE),
                    "--db",
                    str(db),
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(0, code)
            results = json.loads((output / "uat-results.json").read_text("utf-8"))
            manifest = json.loads((output / "manifest.json").read_text("utf-8"))
            self.assertEqual(15, len(results))
            self.assertEqual(0, manifest["network_requests_made"])
            self.assertTrue(manifest["fixture_only"])


if __name__ == "__main__":
    unittest.main()
