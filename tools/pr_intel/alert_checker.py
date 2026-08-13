"""P0 预警检查器：发现 Sev3+ 信号并输出预警，供定时任务调用。

Sev4 15 分钟确认 / Sev3 60 分钟响应（对齐信息源权重体系告警阈值）。
复用 risk_scorer 的评分逻辑，新增「写入 pr_risk_signals + 输出预警摘要」。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.pr_intel.risk_scorer import load_social_posts, score_all, write_risk_signals


def run_alert_check(limit: int = 0, write_db: bool = False) -> dict:
    rows = load_social_posts(limit)
    scored = score_all(rows)
    sev4 = [r for r in scored if r["sev_level"] == "Sev4_危急"]
    sev3 = [r for r in scored if r["sev_level"] == "Sev3_严重"]
    written = write_risk_signals(scored) if write_db else 0
    return {"sev4": sev4, "sev3": sev3, "total": len(scored), "written": written}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P0 Alert Checker")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    result = run_alert_check(args.limit, args.write_db)
    print(f"检查 {result['total']} 条")
    print(f"  Sev4_危急（15分钟确认）: {len(result['sev4'])} 条")
    print(f"  Sev3_严重（60分钟响应）: {len(result['sev3'])} 条")

    if result["sev4"]:
        print("\n── P0 预警（Sev4）──")
        for r in result["sev4"]:
            print(f"  [{r['quality_score']}分] {r['title'][:70]}")
            if r["risk_term"]:
                print(f"       风险词: {r['risk_term']}")
    if result["sev3"]:
        print("\n── P1 预警（Sev3）──")
        for r in result["sev3"][:5]:
            print(f"  [{r['quality_score']}分] {r['title'][:70]}")

    if args.write_db:
        print(f"\n已写入 pr_risk_signals: {result['written']} 条")
