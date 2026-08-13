"""
tools/social/instagram_collector.py — Instagram 内容采集器（TikHub API）

是什么：
  1. 竞品官方账号内容监控（S2需求：竞品社媒营销动作）
  2. 品牌相关 Hashtag 用户讨论（S1需求：Instagram用户讨论）

API 端点（TikHub）：
  账号内容：GET /api/v1/instagram/web/get_user_info_and_media_v2?username=elvie
  Hashtag：  GET /api/v1/instagram/web/hashtag?hashtag=breastpump&count=20
  Reel搜索： GET /api/v1/instagram/web/search_reels?keyword=momcozy

actual_status: CODE_UNVERIFIED（需在部署服务器配置 TIKHUB_API_KEY 后验证）

快速测试：
    python3 tools/social/instagram_collector.py --dry-run
    python3 tools/social/instagram_collector.py --account elvie --limit 10
    python3 tools/social/instagram_collector.py --hashtag breastpump --limit 20
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

# ── 竞品 Instagram 官方账号（S2 需求）─────────────────────────
COMPETITOR_ACCOUNTS = [
    {"brand": "eufy",         "username": "eufyofficial",     "product_line": "pump",             "priority": "P0"},
    {"brand": "elvie",        "username": "elvie",            "product_line": "pump",             "priority": "P0"},
    {"brand": "willow",       "username": "willowpump",       "product_line": "pump",             "priority": "P0"},
    {"brand": "spectra",      "username": "spectrababyusa",   "product_line": "pump",             "priority": "P0"},
    {"brand": "medela",       "username": "medelaofficial",   "product_line": "pump",             "priority": "P0"},
    {"brand": "frida",        "username": "fridababy",        "product_line": "pump",             "priority": "P1"},
    {"brand": "philips_avent","username": "philipsavent",     "product_line": "pump_feeding",     "priority": "P1"},
    {"brand": "baby_brezza",  "username": "babybrezza",       "product_line": "feeding_appliance","priority": "P0"},
    {"brand": "grownsy",      "username": "grownsybaby",      "product_line": "feeding_appliance","priority": "P1"},
    {"brand": "lansinoh",     "username": "lansinoh",         "product_line": "pump",             "priority": "P1"},
    {"brand": "nanit",        "username": "nanit",            "product_line": "monitor",          "priority": "P1"},
    {"brand": "haakaa",       "username": "haakaa_nz",        "product_line": "pump",             "priority": "P2"},
]

# ── S1 用户讨论 Hashtag 清单─────────────────────────────────────
LISTENING_HASHTAGS = [
    {"tag": "breastpump",          "priority": "P0", "purpose": "S1 用户讨论"},
    {"tag": "momcozy",             "priority": "P0", "purpose": "S1 品牌提及"},
    {"tag": "wearablepump",        "priority": "P0", "purpose": "S1 品类讨论"},
    {"tag": "breastfeeding",       "priority": "P1", "purpose": "S1 广泛母乳讨论"},
    {"tag": "exclusivelypumping",  "priority": "P1", "purpose": "S1 排奶社群"},
    {"tag": "pumpingmama",         "priority": "P1", "purpose": "S1 用户自我标注"},
    {"tag": "kleanpal",            "priority": "P0", "purpose": "S1 喂养电器品牌"},
    {"tag": "bottlesterilizer",    "priority": "P1", "purpose": "S1 消毒器话题"},
    {"tag": "workingmom",          "priority": "P2", "purpose": "S1 工作妈妈场景"},
]

BRAND_WATCHLIST = [
    "momcozy", "eufy", "elvie", "willow", "spectra", "medela",
    "frida", "baby brezza", "kleanpal", "lansinoh", "grownsy",
    "wearable pump", "breast pump",
]


def _get_headers() -> dict:
    key = os.environ.get("TIKHUB_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "TIKHUB_API_KEY not set.\n"
            "  设置：export TIKHUB_API_KEY='your-key'"
        )
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _mk_post_id(username: str, post_id: str) -> str:
    raw = f"instagram|{username}|{post_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


def _extract_brand_mentions(text: str) -> list:
    text_lower = text.lower()
    return [b for b in BRAND_WATCHLIST if b in text_lower]


@dataclass
class InstagramPost:
    post_id: str
    platform_code: str = "instagram"
    account_handle: str = ""
    account_type: str = "competitor"
    competitor_brand: str = ""
    content_type: str = "post"
    title: str = ""
    body_text: str = ""
    hashtags: list = field(default_factory=list)
    published_at: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    engagement_rate: float = 0.0
    is_viral_flag: bool = False
    brand_mentions: list = field(default_factory=list)
    country_code: str = "US"
    language: str = "en"
    is_processed: bool = False
    source_type: str = "competitor"   # competitor / hashtag / search

    def __post_init__(self) -> None:
        combined = f"{self.body_text} {' '.join(self.hashtags)}".lower()
        self.brand_mentions = _extract_brand_mentions(combined)
        if self.like_count > 10000 or self.view_count > 100000:
            self.is_viral_flag = True

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_account_posts(username: str, brand: str, limit: int = 20) -> list:
    """采集竞品官方账号帖子（S2 需求）"""
    url = f"{TIKHUB_BASE}/api/v1/instagram/web/get_user_info_and_media_v2"
    params = {"username": username}
    posts = []
    try:
        resp = httpx.get(url, headers=_get_headers(), params=params, timeout=20.0)
        if resp.status_code == 401:
            raise EnvironmentError("TIKHUB_API_KEY 无效（401）")
        if resp.status_code != 200:
            print(f"  [WARN] @{username}: HTTP {resp.status_code}", file=sys.stderr)
            return []
        data = resp.json()
        media_items = (data.get("data") or {}).get("media") or []

        for item in media_items[:limit]:
            post_id = item.get("id") or item.get("pk") or ""
            caption_data = item.get("caption") or {}
            caption = (caption_data.get("text") if isinstance(caption_data, dict)
                       else str(caption_data) if caption_data else "")
            tags = _re.findall(r"#(\w+)", caption)
            like_count = item.get("like_count") or 0
            comment_count = item.get("comment_count") or 0
            view_count = item.get("view_count") or item.get("play_count") or 0
            taken_at = item.get("taken_at") or 0
            published = (datetime.fromtimestamp(int(taken_at), tz=timezone.utc).isoformat()
                         if taken_at else "")
            media_type = item.get("media_type")
            content_type = "reel" if media_type == 2 else "post"

            posts.append(InstagramPost(
                post_id=_mk_post_id(username, str(post_id)),
                account_handle=username,
                account_type="competitor",
                competitor_brand=brand,
                content_type=content_type,
                body_text=caption[:500],
                hashtags=tags[:20],
                published_at=published,
                like_count=like_count,
                comment_count=comment_count,
                view_count=view_count,
                source_type="competitor",
            ))
    except EnvironmentError:
        raise
    except Exception as exc:
        print(f"  [ERROR] fetch_account_posts(@{username}): {exc}", file=sys.stderr)
    return posts


def fetch_hashtag_posts(tag: str, limit: int = 20) -> list:
    """采集 Hashtag 下的用户讨论（S1 需求）"""
    url = f"{TIKHUB_BASE}/api/v1/instagram/web/hashtag"
    params = {"hashtag": tag.lstrip("#"), "count": limit}
    posts = []
    try:
        resp = httpx.get(url, headers=_get_headers(), params=params, timeout=20.0)
        if resp.status_code != 200:
            print(f"  [WARN] #{tag}: HTTP {resp.status_code}", file=sys.stderr)
            return []
        data = resp.json()
        items = (data.get("data") or {}).get("media") or []

        for item in items:
            post_id = item.get("id") or item.get("pk") or ""
            caption_data = item.get("caption") or {}
            caption = (caption_data.get("text") if isinstance(caption_data, dict)
                       else str(caption_data) if caption_data else "")
            tags = _re.findall(r"#(\w+)", caption)
            taken_at = item.get("taken_at") or 0
            published = (datetime.fromtimestamp(int(taken_at), tz=timezone.utc).isoformat()
                         if taken_at else "")
            user = item.get("user") or {}
            username = user.get("username") or ""
            like_count = item.get("like_count") or 0
            comment_count = item.get("comment_count") or 0

            posts.append(InstagramPost(
                post_id=_mk_post_id(f"hashtag_{tag}", str(post_id)),
                account_handle=username,
                account_type="user",
                content_type="post",
                body_text=caption[:500],
                hashtags=tags[:20],
                published_at=published,
                like_count=like_count,
                comment_count=comment_count,
                source_type="hashtag",
            ))
    except EnvironmentError:
        raise
    except Exception as exc:
        print(f"  [ERROR] fetch_hashtag(#{tag}): {exc}", file=sys.stderr)
    return posts


def write_to_db(posts: list) -> int:
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
                 competitor_brand, content_type, body_text, hashtags,
                 published_at, fetched_at, like_count, comment_count,
                 view_count, is_viral_flag, brand_mentions,
                 country_code, language, is_processed)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [
                d["post_id"], d["platform_code"], d["account_handle"], d["account_type"],
                d["competitor_brand"], d["content_type"], d["body_text"], d["hashtags"],
                d["published_at"], d["fetched_at"], d["like_count"], d["comment_count"],
                d["view_count"], d["is_viral_flag"], d["brand_mentions"],
                d["country_code"], d["language"], d["is_processed"],
            ])
            inserted += 1
        except Exception:
            pass
    con.close()
    return inserted


def save_json(posts: list, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = output_dir / f"instagram_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": ts, "post_count": len(posts),
                   "posts": [p.to_dict() for p in posts]},
                  f, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Instagram Collector via TikHub API")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--account", default="", help="竞品账号 username，如 elvie")
    parser.add_argument("--hashtag", default="", help="Hashtag，如 breastpump")
    parser.add_argument("--all-competitors", action="store_true", help="采集全部竞品账号")
    parser.add_argument("--all-hashtags", action="store_true", help="采集全部监听 Hashtag")
    parser.add_argument("--priority", default="P0", choices=["P0", "P1", "P2"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(f"竞品账号: {len(COMPETITOR_ACCOUNTS)} 个")
        for a in COMPETITOR_ACCOUNTS:
            print(f"  [{a['priority']}] @{a['username']:25} ({a['brand']}) [{a['product_line']}]")
        print(f"\n监听 Hashtag: {len(LISTENING_HASHTAGS)} 个")
        for h in LISTENING_HASHTAGS:
            print(f"  [{h['priority']}] #{h['tag']:25} — {h['purpose']}")
        sys.exit(0)

    if not os.environ.get("TIKHUB_API_KEY"):
        print("⚠ TIKHUB_API_KEY 未设置")
        sys.exit(0)

    all_posts = []
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    max_p = priority_order.get(args.priority, 2)

    if args.account:
        brand = next((a["brand"] for a in COMPETITOR_ACCOUNTS
                      if a["username"] == args.account), "unknown")
        print(f"采集 @{args.account} ({brand})...")
        posts = fetch_account_posts(args.account, brand, args.limit)
        print(f"  → {len(posts)} 条")
        all_posts.extend(posts)

    elif args.hashtag:
        print(f"采集 #{args.hashtag}...")
        posts = fetch_hashtag_posts(args.hashtag, args.limit)
        brand_cnt = sum(1 for p in posts if p.brand_mentions)
        print(f"  → {len(posts)} 条, 含品牌提及 {brand_cnt}")
        all_posts.extend(posts)

    elif args.all_hashtags:
        for h in LISTENING_HASHTAGS:
            if priority_order.get(h["priority"], 2) > max_p:
                continue
            print(f"  [{h['priority']}] #{h['tag']}...")
            posts = fetch_hashtag_posts(h["tag"], args.limit)
            brand_cnt = sum(1 for p in posts if p.brand_mentions)
            print(f"       → {len(posts)} 条, 品牌提及 {brand_cnt}")
            all_posts.extend(posts)
            time.sleep(0.5)

    else:
        for acct in COMPETITOR_ACCOUNTS:
            if priority_order.get(acct["priority"], 2) > max_p and not args.all_competitors:
                continue
            print(f"  [{acct['priority']}] @{acct['username']} ({acct['brand']})...")
            posts = fetch_account_posts(acct["username"], acct["brand"], args.limit)
            viral = sum(1 for p in posts if p.is_viral_flag)
            print(f"       → {len(posts)} 条, 高互动 {viral}")
            all_posts.extend(posts)
            time.sleep(0.5)

    print(f"\n总计: {len(all_posts)} 条")
    if all_posts:
        out = save_json(all_posts, OUTPUT_DIR)
        print(f"JSON → {out}")
        if args.write_db:
            inserted = write_to_db(all_posts)
            print(f"DuckDB → {inserted} 条")
