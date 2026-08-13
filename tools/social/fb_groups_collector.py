"""Facebook Groups 采集器（Apify facebook-groups-scraper）。

采集公开 Facebook Groups 的帖子（S1 用户讨论重点平台）。
ToS：法务已放行（2026-08-13），仅采集公开群组，不碰私密群组。
群组 URL 清单待社媒团队提供，先用 GROUPS 占位配置。
actual_status: CODE_UNVERIFIED（待群组 URL 清单后实测）。
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
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.social.dictionary import get_brand_watchlist

PROJ = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJ / "data" / "processed" / "social"
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"

APIFY_BASE = "https://api.apify.com/v2"
APIFY_ACTOR = "apify~facebook-groups-scraper"

GROUPS: list[dict] = [
    # 待社媒团队提供公开群组 URL，格式示例：
    # {"name": "Exclusively Pumping Mamas", "url": "https://www.facebook.com/groups/123456789/"},
]


def _load_zshrc_keys() -> None:
    try:
        content = open(os.path.expanduser("~/.zshrc")).read()
        for m in _re.finditer(r'export (\w+API\w*)="([^"]+)"', content):
            key, val = m.group(1), m.group(2)
            if not os.environ.get(key):
                os.environ[key] = val
    except Exception:
        pass


_load_zshrc_keys()


def _get_apify_token() -> str:
    token = os.environ.get("APIFY_API_KEY", "")
    if not token:
        raise EnvironmentError(
            "APIFY_API_KEY not set. export APIFY_API_KEY='your-token'"
        )
    return token


def _mk_post_id(group: str, post_id: str) -> str:
    raw = f"facebook_group|{group}|{post_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


def _i(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


@dataclass
class FacebookGroupPost:
    post_id: str
    platform_code: str = "facebook"
    account_handle: str = ""
    account_type: str = "user"
    competitor_brand: str = ""
    content_type: str = "post"
    body_text: str = ""
    hashtags: list = field(default_factory=list)
    published_at: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    is_viral_flag: bool = False
    brand_mentions: list = field(default_factory=list)
    post_url: str = ""
    country_code: str = "US"
    language: str = "en"
    is_processed: bool = False

    def __post_init__(self) -> None:
        combined = self.body_text.lower()
        self.brand_mentions = [b for b in get_brand_watchlist() if b in combined]
        self.hashtags = _re.findall(r"#(\w+)", self.body_text)

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_group_posts(group_url: str, group_name: str, limit: int = 20,
                      days_back: int = 30) -> list[FacebookGroupPost]:
    token = _get_apify_token()
    payload = {
        "startUrls": [group_url],
        "resultsLimit": limit,
        "onlyPostsNewerThan": f"{days_back} days",
    }
    resp = httpx.post(
        f"{APIFY_BASE}/acts/{APIFY_ACTOR}/run-sync-get-dataset-items",
        params={"token": token},
        json=payload,
        timeout=180.0,
    )
    if resp.status_code == 401:
        raise EnvironmentError("APIFY_API_KEY 无效（401）")
    if resp.status_code not in (200, 201):
        print(f"  [WARN] {group_name}: HTTP {resp.status_code}", file=sys.stderr)
        return []

    items = resp.json()
    if not isinstance(items, list):
        return []

    posts = []
    for item in items:
        pid = item.get("id") or item.get("postId") or item.get("url", "")[-20:]
        text = item.get("text") or item.get("message") or ""
        ts = item.get("timestamp") or item.get("time") or ""
        if isinstance(ts, (int, float)) and ts > 0:
            published = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
        elif isinstance(ts, str) and ts:
            published = ts
        else:
            published = ""
        posts.append(FacebookGroupPost(
            post_id=_mk_post_id(group_name, str(pid)),
            account_handle=group_name,
            body_text=text[:500],
            published_at=published,
            like_count=_i(item.get("likes") or 0),
            comment_count=_i(item.get("comments") or 0),
            share_count=_i(item.get("shares") or 0),
            post_url=item.get("url") or "",
        ))
    return posts


def write_to_db(posts: list[FacebookGroupPost]) -> int:
    if not posts:
        return 0
    try:
        import duckdb
    except ImportError:
        return 0
    con = duckdb.connect(str(DB_PATH))
    inserted = 0
    for p in posts:
        d = p.to_dict()
        try:
            con.execute("""
                INSERT OR IGNORE INTO social_posts
                (post_id, platform_code, account_handle, account_type,
                 content_type, body_text, hashtags, published_at, fetched_at,
                 like_count, comment_count, share_count, is_viral_flag,
                 brand_mentions, country_code, language, is_processed)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [
                d["post_id"], d["platform_code"], d["account_handle"], d["account_type"],
                d["content_type"], d["body_text"], d["hashtags"], d["published_at"],
                d["fetched_at"], d["like_count"], d["comment_count"], d["share_count"],
                d["is_viral_flag"], d["brand_mentions"], d["country_code"],
                d["language"], d["is_processed"],
            ])
            inserted += 1
        except Exception:
            pass
    con.close()
    return inserted


def save_json(posts: list[FacebookGroupPost], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = output_dir / f"fb_groups_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": ts, "post_count": len(posts),
                   "posts": [p.to_dict() for p in posts]},
                  f, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Facebook Groups Collector via Apify")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--days-back", type=int, default=30)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(f"目标群组: {len(GROUPS)} 个")
        if not GROUPS:
            print("  ⚠ 群组 URL 清单为空，待社媒团队提供公开群组")
            print("  格式示例: https://www.facebook.com/groups/123456789/")
        for g in GROUPS:
            print(f"  {g['name']} → {g['url']}")
        print(f"\nAPI: {APIFY_BASE}/acts/{APIFY_ACTOR}")
        sys.exit(0)

    if not os.environ.get("APIFY_API_KEY"):
        print("⚠ APIFY_API_KEY 未设置")
        sys.exit(0)
    if not GROUPS:
        print("⚠ 群组 URL 清单为空，请先在 GROUPS 里配置公开群组")
        sys.exit(0)

    all_posts: list[FacebookGroupPost] = []
    for g in GROUPS:
        print(f"  {g['name']}...")
        posts = fetch_group_posts(g["url"], g["name"], args.limit, args.days_back)
        print(f"       → {len(posts)} 条")
        all_posts.extend(posts)
        time.sleep(2.0)

    print(f"\n总计: {len(all_posts)} 条")
    if all_posts:
        out = save_json(all_posts, OUTPUT_DIR)
        print(f"JSON → {out}")
        if args.write_db:
            print(f"DuckDB → {write_to_db(all_posts)} 条")
