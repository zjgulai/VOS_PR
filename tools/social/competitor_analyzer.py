"""竞品内容分析器：识别高表现内容（互动量超品类均值 3 倍）。

从 social_posts 读取竞品内容，按品牌聚合，标记高表现内容供 S2 周报使用。
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

PROJ = Path(__file__).resolve().parents[2]
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"


def load_competitor_posts() -> list[dict]:
    import duckdb
    con = duckdb.connect(str(DB_PATH), read_only=True)
    cur = con.execute(
        "SELECT post_id, platform_code, competitor_brand, title, body_text, "
        "like_count, comment_count, view_count FROM social_posts "
        "WHERE competitor_brand IS NOT NULL AND competitor_brand != ''"
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    con.close()
    return rows


def _engagement(p: dict) -> int:
    return (p.get("like_count") or 0) + (p.get("comment_count") or 0) * 2 + (p.get("view_count") or 0) // 100


def analyze(posts: list[dict]) -> list[dict]:
    if not posts:
        return []
    engagements = [_engagement(p) for p in posts]
    baseline = statistics.mean(engagements) if engagements else 0
    threshold = baseline * 3
    high = []
    for p in posts:
        eng = _engagement(p)
        if eng >= threshold and eng > 0:
            high.append({
                "post_id": p["post_id"],
                "brand": p["competitor_brand"],
                "platform": p["platform_code"],
                "title": (p.get("title") or "")[:80],
                "engagement": eng,
                "baseline": round(baseline, 1),
            })
    high.sort(key=lambda x: -x["engagement"])
    return high


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Competitor Content Analyzer")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    posts = load_competitor_posts()
    high = analyze(posts)
    print(f"竞品内容: {len(posts)} 条, 高表现内容: {len(high)} 条")
    for h in high[:args.top]:
        print(f"  [{h['brand']}][{h['platform']}][互动{h['engagement']}] {h['title']}")
