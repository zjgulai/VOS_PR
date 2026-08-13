"""机会识别器：从社媒内容发现竞品讨论缺口与横评对比需求。

横评缺口 = 竞品被讨论但 Momcozy 未同框（竞品获得关注而 Momcozy 缺席的机会点）。
横评对比需求 = 用户主动做品牌对比的内容（"vs"）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.social.dictionary import load_dictionary

PROJ = Path(__file__).resolve().parents[2]
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"


def _competitor_names() -> set[str]:
    d = load_dictionary()
    names = set()
    for line in d["competitors"]["pump"] + d["competitors"]["feeding_appliance"]:
        names.add(line["name"].lower())
        names.add(line["brand_key"].lower())
    return names


def load_posts() -> list[dict]:
    import duckdb
    con = duckdb.connect(str(DB_PATH), read_only=True)
    cur = con.execute(
        "SELECT post_id, platform_code, title, body_text, like_count, "
        "comment_count, brand_mentions, account_type FROM social_posts "
        "WHERE account_type IS NULL OR account_type != 'competitor'"
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    con.close()
    return rows


def find_gaps(posts: list[dict]) -> list[dict]:
    competitors = _competitor_names()
    gaps = []
    for p in posts:
        if p.get("account_type") == "competitor":
            continue
        mentions = [m.lower() for m in (p.get("brand_mentions") or [])]
        if "momcozy" in mentions or "kleanpal" in mentions:
            continue
        text = f"{p.get('title') or ''} {p.get('body_text') or ''}".lower()
        hits = [m for m in competitors if m in text]
        if hits:
            gaps.append({
                "post_id": p["post_id"],
                "platform": p["platform_code"],
                "competitors": hits[:3],
                "title": (p.get("title") or "")[:80],
                "engagement": (p.get("like_count") or 0) + (p.get("comment_count") or 0),
            })
    gaps.sort(key=lambda x: -x["engagement"])
    return gaps


def find_comparisons(posts: list[dict]) -> list[dict]:
    comparisons = []
    for p in posts:
        text = f"{p.get('title') or ''} {p.get('body_text') or ''}".lower()
        if " vs " in text or "versus" in text or " vs." in text:
            comparisons.append({
                "post_id": p["post_id"],
                "platform": p["platform_code"],
                "title": (p.get("title") or "")[:80],
                "engagement": (p.get("like_count") or 0) + (p.get("comment_count") or 0),
            })
    comparisons.sort(key=lambda x: -x["engagement"])
    return comparisons


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PR Opportunity Finder")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    posts = load_posts()
    gaps = find_gaps(posts)
    comparisons = find_comparisons(posts)

    print(f"竞品讨论缺口（Momcozy 缺席）: {len(gaps)} 条")
    for g in gaps[:args.top]:
        print(f"  [{g['platform']}][互动{g['engagement']}] {g['title']}")
        print(f"       竞品: {', '.join(g['competitors'])}")

    print(f"\n横评对比需求（vs 内容）: {len(comparisons)} 条")
    for c in comparisons[:args.top]:
        print(f"  [{c['platform']}][互动{c['engagement']}] {c['title']}")
