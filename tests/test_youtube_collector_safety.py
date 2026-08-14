from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_python(code: str, *, home: Path, extra_pythonpath: Path | None = None) -> subprocess.CompletedProcess[str]:
    module_dir = extra_pythonpath or (home / "_test_modules")
    module_dir.mkdir(parents=True, exist_ok=True)
    httpx_stub = module_dir / "httpx.py"
    if not httpx_stub.exists():
        httpx_stub.write_text(
            "def post(*args, **kwargs):\n    raise AssertionError('network must not be used in V0')\n",
            encoding="utf-8",
        )
    env = os.environ.copy()
    env.pop("APIFY_API_KEY", None)
    env["HOME"] = str(home)
    paths = [str(module_dir), str(ROOT)]
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


class YouTubeCollectorSafetyTests(unittest.TestCase):
    def test_import_does_not_load_api_keys_from_zshrc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".zshrc").write_text(
                'export APIFY_API_KEY="SENTINEL_FROM_PERSONAL_PROFILE"\n',
                encoding="utf-8",
            )
            result = run_python(
                "import os; import tools.social.youtube_collector; "
                "print(os.environ.get('APIFY_API_KEY', 'unset'))",
                home=home,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("unset", result.stdout.strip())

    def test_new_video_does_not_claim_unverified_country_or_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_python(
                textwrap.dedent(
                    """
                    import json
                    from tools.social.youtube_collector import YouTubeVideo
                    video = YouTubeVideo(post_id="fixture")
                    print(json.dumps({"country_code": video.country_code, "language": video.language}))
                    """
                ),
                home=Path(tmp),
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            {"country_code": "unknown", "language": "unknown"},
            json.loads(result.stdout),
        )

    def test_database_write_error_is_not_silently_swallowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            module_dir = Path(tmp) / "modules"
            home.mkdir()
            module_dir.mkdir()
            (module_dir / "duckdb.py").write_text(
                textwrap.dedent(
                    """
                    class Connection:
                        def execute(self, *args, **kwargs):
                            raise RuntimeError("fixture database failure")
                        def close(self):
                            pass
                    def connect(path):
                        return Connection()
                    """
                ),
                encoding="utf-8",
            )
            result = run_python(
                textwrap.dedent(
                    """
                    from tools.social.youtube_collector import YouTubeVideo, write_to_db
                    try:
                        write_to_db([YouTubeVideo(post_id="fixture")])
                    except RuntimeError as exc:
                        print(str(exc))
                    else:
                        print("swallowed")
                    """
                ),
                home=home,
                extra_pythonpath=module_dir,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("failed to write YouTube video fixture", result.stdout)
        self.assertNotIn("swallowed", result.stdout)


if __name__ == "__main__":
    unittest.main()
