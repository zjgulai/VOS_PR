from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "validate_youtube_p0_v1.py"
PENDING_RECORD = ROOT / "tests" / "fixtures" / "youtube_p0" / "v1_preflight_pending.json"


class ValidateYouTubeP0V1CliTests(unittest.TestCase):
    def test_pending_record_returns_no_go_without_attempting_live_request(self) -> None:
        self.assertTrue(SCRIPT.exists(), "validate_youtube_p0_v1.py must exist")
        env = os.environ.copy()
        env.pop("YOUTUBE_API_KEY", None)
        env.pop("GOOGLE_API_KEY", None)

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--record", str(PENDING_RECORD)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(1, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("NO_GO", report["overall_status"])
        self.assertFalse(report["live_request_allowed"])
        self.assertFalse(report["live_request_attempted"])

    def test_live_flag_with_pending_record_is_blocked_before_network(self) -> None:
        self.assertTrue(SCRIPT.exists(), "validate_youtube_p0_v1.py must exist")
        env = os.environ.copy()
        env.pop("YOUTUBE_API_KEY", None)
        env.pop("GOOGLE_API_KEY", None)

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--record",
                str(PENDING_RECORD),
                "--live",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(1, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("NO_GO", report["overall_status"])
        self.assertFalse(report["live_request_allowed"])
        self.assertFalse(report["live_request_attempted"])


if __name__ == "__main__":
    unittest.main()
