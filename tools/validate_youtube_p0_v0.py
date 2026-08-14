#!/usr/bin/env python3
"""运行 YouTube P0 V0 离线安全与数据契约验证。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.social.youtube_p0_contract import build_v0_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate YouTube P0 V0 offline gates")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "youtube_p0" / "v0_fixture.json",
    )
    parser.add_argument(
        "--collector",
        type=Path,
        default=ROOT / "tools" / "social" / "youtube_collector.py",
    )
    args = parser.parse_args()

    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    report = build_v0_report(fixture, args.collector)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
