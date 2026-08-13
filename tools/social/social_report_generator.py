"""社媒周报生成器：生成 Social Media Intelligence Report 草稿（S1-S4 + Actions）。

数据来源：social_posts（用户/竞品内容）+ 竞品分析 + 趋势聚合 + KOL 表。
默认模板填充，--llm 时用 Kimi 增强执行摘要。
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.social.competitor_analyzer import load_competitor_posts, analyze
from tools.social.trend_aggregator import load_rows, aggregate
from tools.pr_intel.risk_scorer import load_social_posts, score_all

PROJ = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJ / "reports" / "social_intel"


def _week_label() -> str:
    today = datetime.now(timezone.utc)
    week_start = today - timedelta(days=today.weekday())
    return week_start.strftime("%Y-%m-%d")


def _s1_user_insights(posts: list[dict], scored: list[dict]) -> dict:
    user_posts = [p for p in posts if p.get("account_type") != "competitor"]
    user_posts.sort(key=lambda p: -((p.get("like_count") or 0) + (p.get("comment_count") or 0)))

    brand_counter: Counter = Counter()
    for p in user_posts:
        for m in (p.get("brand_mentions") or []):
            brand_counter[m] += 1

    score_map = {r["post_id"]: r for r in scored}
    risk_posts = [
        score_map[p["post_id"]] for p in user_posts
        if score_map.get(p["post_id"], {}).get("sev_level") in ("Sev4_危急", "Sev3_严重")
    ]
    return {
        "top_posts": user_posts[:10],
        "brand_distribution": brand_counter.most_common(10),
        "risk_posts": risk_posts,
    }


def _s4_kol() -> dict:
    import duckdb
    con = duckdb.connect(str(PROJ / "data" / "warehouse" / "voc.duckdb"), read_only=True)
    creators = con.execute("SELECT COUNT(*) FROM dim_creator_profiles").fetchone()[0]
    collabs = con.execute("SELECT COUNT(*) FROM dim_competitor_kol_collabs").fetchone()[0]
    con.close()
    return {"creators": creators, "collabs": collabs}


def _collect() -> dict:
    posts = load_social_posts()
    scored = score_all(posts)
    s1 = _s1_user_insights(posts, scored)
    high = analyze(load_competitor_posts())
    hashtags, bgms = aggregate(load_rows())
    kol = _s4_kol()
    return {
        "week": _week_label(),
        "total": len(posts),
        "s1": s1,
        "high": high,
        "hashtags": hashtags[:10],
        "bgms": bgms[:10],
        "kol": kol,
    }


def render_report(data: dict, summary: str = "") -> str:
    s1 = data["s1"]
    lines = [
        f"# Social Media Intelligence Report — Week of {data['week']}",
        "",
        "## 执行摘要",
        summary or f"- 本周采集 {data['total']} 条内容，风险信号 {len(s1['risk_posts'])} 条。",
        "",
        "## S1 用户讨论洞察",
        f"- 品牌提及分布: {', '.join(f'{k}({v})' for k, v in s1['brand_distribution'][:8])}",
        "| 话题 | 平台 | 互动量 |",
        "|------|------|--------|",
    ]
    for p in s1["top_posts"][:10]:
        eng = (p.get("like_count") or 0) + (p.get("comment_count") or 0)
        lines.append(f"| {(p.get('title') or '')[:50]} | {p['platform_code']} | {eng} |")

    if s1["risk_posts"]:
        lines += ["", "潜在风险:", "| 风险 | 等级 | 分数 |", "|------|------|------|"]
        for r in s1["risk_posts"]:
            lines.append(f"| {r['title'][:50]} | {r['sev_level']} | {r['quality_score']} |")

    lines += [
        "",
        "## S2 竞品社媒动态",
        "| 品牌 | 平台 | 互动量 | 内容 |",
        "|------|------|--------|------|",
    ]
    for h in data["high"][:10]:
        lines.append(f"| {h['brand']} | {h['platform']} | {h['engagement']} | {h['title'][:50]} |")

    lines += [
        "",
        "## S3 热点趋势",
        "| Hashtag | 频次 | 互动量 |",
        "|---------|------|--------|",
    ]
    for h in data["hashtags"][:5]:
        lines.append(f"| #{h['tag']} | {h['count']} | {h['engagement']} |")
    if data["bgms"]:
        lines += ["", "热门 BGM:", ]
        lines += [f"- {b['title'][:50]} ({b['count']} 次)" for b in data["bgms"][:5]]

    lines += [
        "",
        "## S4 KOL 动态",
        f"- Creator 档案: {data['kol']['creators']} 条，竞品合作记录: {data['kol']['collabs']} 条",
        "- 待 KOL 关注池清单（社媒团队填写 PMO Excel）后启动采集",
        "",
        "## Social Media Actions（本周建议）",
        "| 行动类型 | 具体建议 | 优先级 |",
        "|----------|----------|--------|",
        "| 风险回应 | 审核 S1 潜在风险信号 | P0 |",
        "| 趋势跟进 | 评估 S3 热门 Hashtag 是否适合品牌 | P1 |",
        "",
        "---",
        "*草稿由 AI 生成，需团队 review 后使用*",
    ]
    return "\n".join(lines)


def _llm_summary(data: dict) -> str:
    from tools.llm.client import complete
    prompt = (
        f"本周社媒情报：总内容 {data['total']} 条、风险 {len(data['s1']['risk_posts'])} 条、"
        f"竞品高表现 {len(data['high'])} 条。请用 4 句话写执行摘要：用户讨论热点、"
        "竞品动态、趋势机会、本周建议。"
    )
    try:
        return complete(prompt, task_type="generate_report")
    except Exception:
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Social Report Generator")
    parser.add_argument("--llm", action="store_true", help="用 Kimi 增强执行摘要")
    args = parser.parse_args()

    data = _collect()
    summary = _llm_summary(data) if args.llm else ""
    report = render_report(data, summary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f"{data['week']}_Social_Intel.md"
    out.write_text(report, encoding="utf-8")
    print(f"社媒周报生成 → {out.relative_to(PROJ)}")
    print(f"  数据: {data['total']} 帖, 风险={len(data['s1']['risk_posts'])}, "
          f"竞品高表现={len(data['high'])}, Hashtag={len(data['hashtags'])}")
