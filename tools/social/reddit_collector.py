"""
tools/social/reddit_collector.py — Reddit 帖子采集器（TikHub Dynamic Search API）

是什么：通过 TikHub fetch_dynamic_search 采集母婴相关 Reddit 帖子
实际字段：postTitle / content.markdown / authorInfo.name / commentCount / score
输出：写入 DuckDB social_posts 表

actual_status: LIVE（2026-08-12 验证：48条真实帖子，42条含品牌提及）
"""
from __future__ import annotations

import hashlib
import json
import os
import re as _re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))

def _load_zshrc_keys():
    try:
        content = open(os.path.expanduser("~/.zshrc")).read()
        for m in _re.finditer(r'export (\w+API\w*)="([^"]+)"', content):
            k, v = m.group(1), m.group(2)
            if not os.environ.get(k):
                os.environ[k] = v
    except Exception:
        pass
_load_zshrc_keys()

PROJ = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJ / "data" / "processed" / "social"
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"
TIKHUB_BASE = "https://api.tikhub.io"

SEARCH_QUERIES = [
    "momcozy breast pump review",
    "momcozy vs medela vs willow pump",
    "wearable breast pump recommendation 2026",
    "breast pump hands free pumping pain",
    "breastfeeding pump working mom tips",
    "momcozy issues problems complaint",
    "best breast pump insurance covered",
    "breast pump supply insurance medicaid",
    "momcozy paying fake reviews",
    "wearable pump leak output low",
]

BRAND_WATCHLIST = [
    "momcozy", "medela", "willow", "elvie", "spectra", "lansinoh",
    "babybuddha", "nanit", "owlet", "frida", "eufy",
    "breast pump", "wearable pump", "kleanpal", "m5", "s12", "v1 pro",
]


def _get_headers() -> dict:
    key = os.environ.get("TIKHUB_API_KEY","")
    if not key:
        raise EnvironmentError("TIKHUB_API_KEY not set")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _extract_text(field) -> str:
    if not field:
        return ""
    if isinstance(field, str):
        return field[:1000]
    if isinstance(field, dict):
        return (field.get("markdown") or field.get("text") or str(field))[:1000]
    return str(field)[:1000]


def _find_posts(obj) -> list:
    posts = []
    if isinstance(obj, dict):
        if obj.get("__typename") == "SubredditPost":
            posts.append(obj)
            return posts
        for v in obj.values():
            posts.extend(_find_posts(v))
    elif isinstance(obj, list):
        for item in obj:
            posts.extend(_find_posts(item))
    return posts


def _parse_post(p: dict) -> dict:
    pid = p.get("id","")
    title = p.get("postTitle") or p.get("title") or ""
    body = _extract_text(p.get("content") or p.get("selfText") or "")
    combined = f"{title} {body}".lower()
    brands = [b for b in BRAND_WATCHLIST if b in combined]

    sub = p.get("subreddit") or {}
    subreddit = sub.get("name","") if isinstance(sub, dict) else ""

    auth = p.get("authorInfo") or p.get("author") or ""
    author = auth.get("name","") if isinstance(auth, dict) else str(auth)

    return {
        "post_id": hashlib.sha1(f"reddit|{pid}".encode()).hexdigest()[:20],
        "platform_code": "reddit",
        "account_handle": author or "[deleted]",
        "account_type": "user",
        "content_type": "thread",
        "title": title[:300],
        "body_text": body,
        "published_at": str(p.get("createdAt") or ""),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "like_count": int(p.get("score") or 0),
        "comment_count": int(p.get("commentCount") or 0),
        "is_viral_flag": int(p.get("score") or 0) > 100,
        "brand_mentions": brands,
        "country_code": "US",
        "language": p.get("languageCode") or "en",
        "is_processed": False,
    }


def fetch_by_keywords(queries: list, limit_per_query: int = 10) -> list:
    all_rows = []
    seen_ids: set = set()
    for query in queries:
        try:
            resp = httpx.get(
                f"{TIKHUB_BASE}/api/v1/reddit/app/fetch_dynamic_search",
                headers=_get_headers(),
                params={"query": query},
                timeout=15.0,
            )
            if resp.status_code != 200:
                print(f"  [WARN] {query}: HTTP {resp.status_code}", file=sys.stderr)
                continue
            posts = _find_posts(resp.json())
            added = 0
            for p in posts[:limit_per_query]:
                pid = p.get("id","")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                all_rows.append(_parse_post(p))
                added += 1
            time.sleep(0.3)
        except Exception as exc:
            print(f"  [ERROR] {query}: {exc}", file=sys.stderr)
    return all_rows


def write_to_db(rows: list) -> int:
    if not rows:
        return 0
    try:
        import duckdb
    except ImportError:
        return 0
    con = duckdb.connect(str(DB_PATH))
    inserted = 0
    for r in rows:
        try:
            con.execute("""
                INSERT OR IGNORE INTO social_posts
                (post_id, platform_code, account_handle, account_type,
                 content_type, title, body_text, published_at, fetched_at,
                 like_count, comment_count, is_viral_flag, brand_mentions,
                 country_code, language, is_processed)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [r["post_id"], r["platform_code"], r["account_handle"], r["account_type"],
                  r["content_type"], r["title"], r["body_text"], r["published_at"], r["fetched_at"],
                  r["like_count"], r["comment_count"], r["is_viral_flag"], r["brand_mentions"],
                  r["country_code"], r["language"], r["is_processed"]])
            inserted += 1
        except Exception:
            pass
    con.close()
    return inserted


def save_json(rows: list, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = output_dir / f"reddit_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": ts, "post_count": len(rows), "posts": rows},
                  f, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reddit Collector via TikHub API")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(f"搜索关键词: {len(SEARCH_QUERIES)} 个")
        for q in SEARCH_QUERIES:
            print(f"  {q}")
        sys.exit(0)

    rows = fetch_by_keywords(SEARCH_QUERIES, limit_per_query=args.limit)
    brand_count = sum(1 for r in rows if r["brand_mentions"])
    print(f"总计: {len(rows)} 条, 含品牌提及: {brand_count}")

    out = save_json(rows, OUTPUT_DIR)
    print(f"JSON → {out}")
    if args.write_db:
        inserted = write_to_db(rows)
        print(f"DuckDB → {inserted} 条")
