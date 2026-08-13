"""趋势聚合器：聚合 hashtags 与 BGM，输出 Top 列表供 S3 趋势洞察。

从 social_posts 的 hashtags / bgm_title 字段统计频次与互动。
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

PROJ = Path(__file__).resolve().parents[2]
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"


def load_rows() -> list[dict]:
    import duckdb
    con = duckdb.connect(str(DB_PATH), read_only=True)
    cur = con.execute(
        "SELECT platform_code, hashtags, bgm_title, bgm_author, like_count, comment_count FROM social_posts"
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    con.close()
    return rows


def aggregate(rows: list[dict]) -> tuple[list, list]:
    hashtag_freq: Counter = Counter()
    hashtag_eng: Counter = Counter()
    bgm_freq: Counter = Counter()
    for r in rows:
        eng = (r.get("like_count") or 0) + (r.get("comment_count") or 0)
        for h in (r.get("hashtags") or []):
            tag = h.lstrip("#").lower()
            hashtag_freq[tag] += 1
            hashtag_eng[tag] += eng
        if r.get("bgm_title"):
            bgm_freq[r["bgm_title"]] += 1

    hashtags = [
        {"tag": tag, "count": hashtag_freq[tag], "engagement": hashtag_eng[tag]}
        for tag in hashtag_freq
    ]
    hashtags.sort(key=lambda x: -x["count"])
    bgms = [{"title": t, "count": c} for t, c in bgm_freq.most_common(10)]
    return hashtags, bgms


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trend Aggregator")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    rows = load_rows()
    hashtags, bgms = aggregate(rows)
    print(f"Top {args.top} Hashtag:")
    for h in hashtags[:args.top]:
        print(f"  #{h['tag']:30} {h['count']} 次, 互动 {h['engagement']}")
    print(f"\nTop BGM:")
    for b in bgms[:args.top]:
        print(f"  {b['title'][:40]:42} {b['count']} 次")
