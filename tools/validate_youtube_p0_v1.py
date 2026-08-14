#!/usr/bin/env python3
"""运行 YouTube P0 V1 真实只读连接前置检查；本命令不发起外部请求。"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.social.youtube_p0_v1 import evaluate_v1_preflight
from tools.social.youtube_official_connector import (
    YouTubeOfficialClient,
    run_v1_readonly_smoke,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate YouTube P0 V1 preflight gates")
    parser.add_argument(
        "--record",
        type=Path,
        default=ROOT / "config" / "youtube_p0_v1_preflight.json",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run the official read-only smoke only after every preflight gate passes",
    )
    args = parser.parse_args()

    record = json.loads(args.record.read_text(encoding="utf-8"))
    report = evaluate_v1_preflight(record, environ=os.environ)
    report["live_request_attempted"] = False
    if args.live and report["live_request_allowed"]:
        env_var = record["secret_source"]["env_var"]
        with YouTubeOfficialClient(api_key=os.environ[env_var]) as client:
            report = run_v1_readonly_smoke(
                record,
                environ=os.environ,
                client=client,
            )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["overall_status"] in {"READY", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
