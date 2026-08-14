from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "validate_youtube_p0_v0.py"
FIXTURE = ROOT / "tests" / "fixtures" / "youtube_p0" / "v0_fixture.json"
COLLECTOR = ROOT / "tools" / "social" / "youtube_collector.py"


class ValidateYouTubeP0V0CliTests(unittest.TestCase):
    def run_cli(self, collector: Path) -> subprocess.CompletedProcess[str]:
        self.assertTrue(SCRIPT.exists(), "validate_youtube_p0_v0.py must exist")
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--fixture",
                str(FIXTURE),
                "--collector",
                str(collector),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_returns_pass_report_for_hardened_collector(self) -> None:
        result = self.run_cli(COLLECTOR)

        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("PASS", report["overall_status"])
        self.assertTrue(report["fixture_only"])

    def test_cli_returns_no_go_for_unsafe_collector(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            unsafe = Path(tmp) / "unsafe_collector.py"
            unsafe.write_text(
                textwrap.dedent(
                    '''
                    from dataclasses import dataclass

                    try:
                        open("~/.zshrc").read()
                    except Exception:
                        pass

                    @dataclass
                    class Video:
                        country_code: str = "US"
                        language: str = "en"
                    '''
                ),
                encoding="utf-8",
            )
            result = self.run_cli(unsafe)

        self.assertEqual(1, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("NO_GO", report["overall_status"])
        self.assertEqual("FAIL", report["checks"]["secret_and_profile_safety"]["status"])
        self.assertEqual("FAIL", report["checks"]["silent_exception_safety"]["status"])


if __name__ == "__main__":
    unittest.main()
