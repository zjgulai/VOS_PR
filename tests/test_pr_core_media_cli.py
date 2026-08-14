from __future__ import annotations

import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.pr_intel.core_media.cli import main


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pr_core_media/core_media_pool_synthetic.xlsx"
SHEET = "吸奶器核心媒体池"
SCOPE = ROOT / "config/pr_core_media_p0_scope.json"
CAPABILITIES = ROOT / "config/pr_core_media_source_capabilities.json"


class CoreMediaCliTests(unittest.TestCase):
    def test_preview_workbook_writes_audit_json_without_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "preview.json"
            rc = main(
                [
                    "preview-workbook",
                    "--input",
                    str(FIXTURE),
                    "--sheet",
                    SHEET,
                    "--import-version",
                    "fixture-cli-v1",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(0, rc)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(2, payload["counts"]["outlets"])
            self.assertEqual(3, payload["counts"]["journalists"])
            self.assertFalse(any(Path(temp_dir).glob("*.duckdb")))

    def test_approve_requires_explicit_registry_confirmation(self) -> None:
        with self.assertRaises(SystemExit):
            main(
                [
                    "approve-workbook",
                    "--input",
                    str(FIXTURE),
                    "--sheet",
                    SHEET,
                    "--import-version",
                    "fixture-cli-v1",
                    "--db",
                    "/tmp/not-used.duckdb",
                    "--approved-by-role",
                    "admin",
                    "--gate0-decision-ref",
                    "/tmp/not-used.md",
                ]
            )

    def test_validate_sources_offline_reports_no_network_and_live_blocked(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = main(
                [
                    "validate-sources",
                    "--scope",
                    str(SCOPE),
                    "--capabilities",
                    str(CAPABILITIES),
                    "--offline",
                ]
            )

        self.assertEqual(0, rc)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(11, payload["summary"]["covered_scope_outlets"])
        self.assertEqual(0, payload["summary"]["network_requests_made"])
        self.assertFalse(payload["summary"]["live_readonly_smoke_allowed"])


if __name__ == "__main__":
    unittest.main()
