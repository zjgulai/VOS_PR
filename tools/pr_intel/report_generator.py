"""PR 周报生成器：从仓库数据生成 Markdown 周报草稿。

数据来源：pr_risk_signals（P0/P1 预警）+ social_posts（竞品/用户动态）+ 机会识别。
默认模板填充，--llm 时用 Kimi 增强执行摘要。
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.pr_intel.risk_scorer import load_social_posts, score_all
from tools.pr_intel.opportunity_finder import find_gaps
from tools.social.competitor_analyzer import load_competitor_posts, analyze

PROJ = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJ / "reports" / "pr_intel"


def _week_label() -> str:
    today = datetime.now(timezone.utc)
    week_start = today - timedelta(days=today.weekday())
    return f"{week_start.strftime('%Y-%m-%d')}"


def _collect() -> dict:
    posts = load_social_posts()
    scored = score_all(posts)
    sev4 = [r for r in scored if r["sev_level"] == "Sev4_危急"]
    sev3 = [r for r in scored if r["sev_level"] == "Sev3_严重"]
    high = analyze(load_competitor_posts())
    gaps = find_gaps(posts)
    return {
        "week": _week_label(),
        "total_posts": len(posts),
        "sev4": sev4,
        "sev3": sev3,
        "high_competitor": high,
        "gaps": gaps,
    }


def render_report(data: dict, summary: str = "") -> str:
    lines = [
        f"# PR Intelligence Report — Week of {data['week']}",
        "",
        "## 执行摘要",
        summary or f"- 本周采集 {data['total_posts']} 条内容，P0 风险 {len(data['sev4'])} 条，P1 风险 {len(data['sev3'])} 条。",
        "",
        "## P0/P1 风险预警",
        "| 风险 | 等级 | 风险分 | 建议行动 |",
        "|------|------|--------|----------|",
    ]
    for r in data["sev4"] + data["sev3"]:
        lines.append(
            f"| {r['title'][:40]} | {r['sev_level']} | {r['quality_score']} | 待 PR 审核 |"
        )

    lines += [
        "",
        "## 竞品高表现内容",
        "| 品牌 | 平台 | 互动量 | 内容 |",
        "|------|------|--------|------|",
    ]
    for h in data["high_competitor"][:10]:
        lines.append(
            f"| {h['brand']} | {h['platform']} | {h['engagement']} | {h['title'][:50]} |"
        )

    lines += [
        "",
        "## 机会清单（竞品讨论缺口）",
        "| 平台 | 竞品 | 互动量 | 内容 |",
        "|------|------|--------|------|",
    ]
    for g in data["gaps"][:10]:
        lines.append(
            f"| {g['platform']} | {', '.join(g['competitors'])} | {g['engagement']} | {g['title'][:50]} |"
        )

    lines += [
        "",
        "## PR Actions（本周建议）",
        "| 行动 | 负责人 | 截止 | 所需 |",
        "|------|--------|------|------|",
        "| 审核 P0 风险并确认回应口径 | PR Analyst | 本周 | 原文链接 |",
        "| 评估竞品讨论缺口的机会点 | PR Analyst | 本周 | 缺口清单 |",
        "",
        "---",
        "*草稿由 AI 生成，所有引用来源可追溯，对外行动须 Analyst 审批后执行*",
    ]
    return "\n".join(lines)


def _llm_summary(data: dict) -> str:
    from tools.llm.client import complete
    prompt = (
        f"本周 PR 情报数据：P0 风险 {len(data['sev4'])} 条、P1 风险 {len(data['sev3'])} 条、"
        f"竞品高表现内容 {len(data['high_competitor'])} 条、竞品讨论缺口 {len(data['gaps'])} 条。"
        "请用 4 句话写执行摘要：媒体和行业发生了什么、对 Momcozy 意味着什么、"
        "本周最重要的机会、本周最需要关注的风险。"
    )
    try:
        return complete(prompt, task_type="generate_report")
    except Exception:
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PR Report Generator")
    parser.add_argument("--llm", action="store_true", help="用 Kimi 增强执行摘要")
    args = parser.parse_args()

    data = _collect()
    summary = _llm_summary(data) if args.llm else ""
    report = render_report(data, summary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f"{data['week']}_PR_Intelligence.md"
    out.write_text(report, encoding="utf-8")
    print(f"周报生成 → {out.relative_to(PROJ)}")
    print(f"  数据: {data['total_posts']} 帖, P0={len(data['sev4'])}, P1={len(data['sev3'])}, "
          f"竞品高表现={len(data['high_competitor'])}, 缺口={len(data['gaps'])}")
