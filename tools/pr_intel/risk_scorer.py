"""风险评分器：实现五维公式（S/R/B/T/K）+ Sev 分级。

公式：score = S*0.35 + R*0.25 + B*0.20 + T*0.10 + K
阈值：Sev4>=75 | Sev3 60-74 且互动>50 | Sev2 40-59 | Sev1 25-39 | Sev0<25
来源：docs/信息源质量权重体系v1.0.md（Q9/Q10 已确认）
品牌/风险词：从 config/competitor_dictionary.json 读取。
"""
from __future__ import annotations

import argparse
import math
import os
import re as _re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.social.dictionary import get_brand_watchlist, get_risk_keywords

PROJ = Path(__file__).resolve().parents[2]
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"

SOURCE_AUTHORITY = {
    "reddit": 0.60, "tiktok": 0.40, "youtube": 0.55, "instagram": 0.38,
    "facebook": 0.45, "facebook_groups": 0.45,
    "cpsc": 1.00, "fda": 1.00, "ftc": 0.90, "classaction": 0.92,
    "babylist": 0.82, "wirecutter": 0.90, "consumer_reports": 0.92,
    "globenewswire": 0.45, "prnewswire": 0.45,
}

P90_ENGAGEMENT = {"reddit": 390.0, "tiktok": 11568.0, "default": 300.0}


def _score_reach(platform: str, like_count: int, comment_count: int) -> float:
    engagement = 1 + (like_count or 0) + (comment_count or 0) * 2
    p90 = P90_ENGAGEMENT.get(platform, P90_ENGAGEMENT["default"])
    return min(1.0, math.log(engagement) / math.log(1 + p90))


def _score_brand(brand_mentions: list[str], title: str) -> float:
    mentions = [b.lower() for b in (brand_mentions or [])]
    title_lower = (title or "").lower()
    if "momcozy" in mentions or "kleanpal" in mentions:
        return 1.00
    if "momcozy" in title_lower or "kleanpal" in title_lower:
        return 0.90
    t1 = {"eufy", "elvie", "willow", "spectra", "medela", "frida", "grownsy"}
    if any(b in mentions for b in t1):
        return 0.85
    if any(b in mentions for b in ("wearable pump", "m5")):
        return 0.65
    if "breast pump" in mentions:
        return 0.45
    if "breast pump" in title_lower:
        return 0.40
    return 0.30


def _score_time(published_at: str) -> float:
    if not published_at:
        return 0.85
    try:
        pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return 0.85
    days = (datetime.now(timezone.utc) - pub.astimezone(timezone.utc)).days
    if days <= 7:
        return 1.00
    if days <= 30:
        return 0.90
    if days <= 90:
        return 0.70
    return 0.50


def _score_risk_boost(title: str, body: str) -> tuple[float, str]:
    text = f"{title or ''} {body or ''}".lower()
    best_boost = 0.0
    best_term = ""
    for kw in get_risk_keywords():
        term = kw["term"].lower()
        if _re.search(r"\b" + _re.escape(term) + r"\b", text) and kw["boost"] > best_boost:
            best_boost = kw["boost"]
            best_term = kw["term"]
    return best_boost, best_term


def score_content(row: dict) -> dict:
    platform = (row.get("platform_code") or "").lower()
    title = row.get("title") or ""
    body = row.get("body_text") or ""
    mentions = row.get("brand_mentions") or []

    s = SOURCE_AUTHORITY.get(platform, 0.40)
    r = _score_reach(platform, row.get("like_count") or 0, row.get("comment_count") or 0)
    b = _score_brand(mentions, title)
    t = _score_time(str(row.get("published_at") or ""))
    k, risk_term = _score_risk_boost(title, body)

    score = s * 0.35 + r * 0.25 + b * 0.20 + t * 0.10 + k
    score_100 = round(min(1.0, score) * 100, 1)
    engagement = (row.get("like_count") or 0) + (row.get("comment_count") or 0)

    if score_100 >= 75:
        sev = "Sev4_危急"
    elif score_100 >= 60 and engagement > 50:
        sev = "Sev3_严重"
    elif score_100 >= 40:
        sev = "Sev2_升级"
    elif score_100 >= 25:
        sev = "Sev1_关注"
    else:
        sev = "Sev0_观察"

    return {
        "post_id": row.get("post_id"),
        "platform_code": platform,
        "title": title,
        "quality_score": score_100,
        "sev_level": sev,
        "risk_term": risk_term,
        "S": round(s, 2), "R": round(r, 2), "B": round(b, 2),
        "T": round(t, 2), "K": k,
    }


def score_all(rows: list[dict]) -> list[dict]:
    return [score_content(r) for r in rows]


def load_social_posts(limit: int = 0) -> list[dict]:
    import duckdb
    con = duckdb.connect(str(DB_PATH), read_only=True)
    q = ("SELECT post_id, platform_code, title, body_text, published_at, "
         "like_count, comment_count, brand_mentions, account_type FROM social_posts "
         "WHERE is_processed = FALSE OR is_processed IS NULL")
    if limit:
        q += f" LIMIT {limit}"
    cur = con.execute(q)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    con.close()
    return rows


def write_risk_signals(scored: list[dict]) -> int:
    import duckdb
    con = duckdb.connect(str(DB_PATH))
    inserted = 0
    for r in scored:
        if r["sev_level"] not in ("Sev4_危急", "Sev3_严重"):
            continue
        try:
            con.execute("""
                INSERT OR IGNORE INTO pr_risk_signals
                (signal_id, article_id, signal_type, severity_score,
                 source_authority, brand_proximity, final_risk_score, sev_level, created_at)
                VALUES (?,?,?,?,?,?,?,?,now())
            """, [
                r["post_id"], r["post_id"], r.get("risk_term") or "reputational",
                r["S"] * 100, r["S"], r["B"], r["quality_score"], r["sev_level"],
            ])
            inserted += 1
        except Exception:
            pass
    con.close()
    return inserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PR/Social Risk Scorer")
    parser.add_argument("--limit", type=int, default=0, help="限制评分条数，0=全部未处理")
    parser.add_argument("--write-db", action="store_true", help="Sev3+ 写入 pr_risk_signals")
    args = parser.parse_args()

    rows = load_social_posts(args.limit)
    scored = score_all(rows)
    scored.sort(key=lambda x: -x["quality_score"])

    sev_counts: dict[str, int] = {}
    for r in scored:
        sev_counts[r["sev_level"]] = sev_counts.get(r["sev_level"], 0) + 1
    print(f"评分完成: {len(scored)} 条")
    for sev in ("Sev4_危急", "Sev3_严重", "Sev2_升级", "Sev1_关注", "Sev0_观察"):
        if sev in sev_counts:
            print(f"  {sev}: {sev_counts[sev]}")
    print()
    for r in scored[:10]:
        if r["sev_level"] in ("Sev4_危急", "Sev3_严重"):
            print(f"  [{r['sev_level']}][{r['quality_score']}分] {r['title'][:60]}")

    if args.write_db:
        n = write_risk_signals(scored)
        print(f"\n已写入 pr_risk_signals: {n} 条")
