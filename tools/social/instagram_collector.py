"""Instagram 采集器（TikHub 官方 SDK）。

采集竞品官方账号帖子（S2）与品牌 Hashtag 用户讨论（S1）。
正确流程：instagram_v3.get_user_id_by_username -> instagram_v1.fetch_user_posts。
品牌匹配与竞品账号均从 config/competitor_dictionary.json 读取。
actual_status: LIVE（2026-08-13 实测 elvie 返回 4 帖）。
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

sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.social.dictionary import get_brand_watchlist, get_competitor_accounts

PROJ = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJ / "data" / "processed" / "social"
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"

LISTENING_HASHTAGS = [
    {"tag": "breastpump", "priority": "P0", "purpose": "S1 用户讨论"},
    {"tag": "momcozy", "priority": "P0", "purpose": "S1 品牌提及"},
    {"tag": "wearablepump", "priority": "P0", "purpose": "S1 品类讨论"},
    {"tag": "breastfeeding", "priority": "P1", "purpose": "S1 广泛母乳讨论"},
    {"tag": "exclusivelypumping", "priority": "P1", "purpose": "S1 排奶社群"},
    {"tag": "kleanpal", "priority": "P0", "purpose": "S1 喂养电器品牌"},
    {"tag": "bottlesterilizer", "priority": "P1", "purpose": "S1 消毒器话题"},
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


def _get_client():
    from tikhub import TikHub
    api_key = os.environ.get("TIKHUB_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "TIKHUB_API_KEY not set. export TIKHUB_API_KEY='your-key'"
        )
    return TikHub(api_key=api_key)


def _mk_post_id(username: str, post_id: str) -> str:
    raw = f"instagram|{username}|{post_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


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
    source_type: str = "competitor"

    def __post_init__(self) -> None:
        combined = f"{self.body_text} {' '.join(self.hashtags)}".lower()
        self.brand_mentions = [b for b in get_brand_watchlist() if b in combined]
        if self.like_count > 10000 or self.view_count > 100000:
            self.is_viral_flag = True

    def to_dict(self) -> dict:
        return asdict(self)


def _parse_item(item: dict, username: str, brand: str, source_type: str) -> InstagramPost:
    caption = item.get("caption") or {}
    caption_text = caption.get("text", "") if isinstance(caption, dict) else str(caption)
    tags = _re.findall(r"#(\w+)", caption_text)
    taken = item.get("taken_at") or 0
    published = (
        datetime.fromtimestamp(int(taken), tz=timezone.utc).isoformat() if taken else ""
    )
    media_type = item.get("media_type")
    content_type = "reel" if media_type == 2 else "post"
    code = item.get("code") or ""
    post_id = str(item.get("pk") or item.get("id") or "")

    return InstagramPost(
        post_id=_mk_post_id(username, post_id),
        account_handle=username,
        account_type="competitor" if source_type == "competitor" else "user",
        competitor_brand=brand,
        content_type=content_type,
        body_text=caption_text[:500],
        hashtags=tags[:20],
        published_at=published,
        view_count=int(item.get("play_count") or item.get("view_count") or 0),
        like_count=int(item.get("like_count") or 0),
        comment_count=int(item.get("comment_count") or 0),
        source_type=source_type,
    )


def fetch_account_posts(username: str, brand: str, limit: int = 20) -> list[InstagramPost]:
    client = _get_client()
    try:
        uid_resp = client.instagram_v3.get_user_id_by_username(username=username)
        uid = (uid_resp.get("data") or {}).get("user_id") if isinstance(uid_resp, dict) else None
        if not uid:
            print(f"  [WARN] @{username}: 无法解析 user_id", file=sys.stderr)
            return []
        posts_resp = client.instagram_v1.fetch_user_posts(user_id=str(uid), count=limit)
        data = posts_resp.get("data") if isinstance(posts_resp, dict) else {}
        items = data.get("items") or []
        return [_parse_item(it, username, brand, "competitor") for it in items]
    except Exception as exc:
        print(f"  [ERROR] fetch_account_posts(@{username}): {exc}", file=sys.stderr)
        return []


def fetch_hashtag_posts(tag: str, limit: int = 20) -> list[InstagramPost]:
    client = _get_client()
    try:
        resp = client.instagram_v1.fetch_hashtag_posts(hashtag=tag.lstrip("#"))
        data = resp.get("data") if isinstance(resp, dict) else {}
        items = data.get("items") or []
        posts = []
        for it in items[:limit]:
            user = it.get("user") or {}
            username = user.get("username", "") if isinstance(user, dict) else ""
            posts.append(_parse_item(it, username or f"hashtag_{tag}", "", "hashtag"))
        return posts
    except Exception as exc:
        print(f"  [ERROR] fetch_hashtag_posts(#{tag}): {exc}", file=sys.stderr)
        return []


def write_to_db(posts: list[InstagramPost]) -> int:
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


def save_json(posts: list[InstagramPost], output_dir: Path) -> Path:
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
    parser = argparse.ArgumentParser(description="Instagram Collector via TikHub SDK")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--account", default="", help="竞品账号 username，如 elvie")
    parser.add_argument("--hashtag", default="", help="Hashtag，如 breastpump")
    parser.add_argument("--all-competitors", action="store_true")
    parser.add_argument("--all-hashtags", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    accounts = get_competitor_accounts("instagram")

    if args.dry_run:
        print(f"竞品账号（来自词典）: {len(accounts)} 个")
        for a in accounts:
            print(f"  [{a['priority']}] @{a['handle']:25} ({a['name']})")
        print(f"\n监听 Hashtag: {len(LISTENING_HASHTAGS)} 个")
        for h in LISTENING_HASHTAGS:
            print(f"  [{h['priority']}] #{h['tag']:25} — {h['purpose']}")
        sys.exit(0)

    if not os.environ.get("TIKHUB_API_KEY"):
        print("⚠ TIKHUB_API_KEY 未设置")
        sys.exit(0)

    all_posts: list[InstagramPost] = []
    if args.account:
        brand = next((a["brand"] for a in accounts if a["handle"] == args.account), "unknown")
        print(f"采集 @{args.account} ({brand})...")
        all_posts = fetch_account_posts(args.account, brand, args.limit)
    elif args.hashtag:
        print(f"采集 #{args.hashtag}...")
        all_posts = fetch_hashtag_posts(args.hashtag, args.limit)
    elif args.all_hashtags:
        for h in LISTENING_HASHTAGS:
            posts = fetch_hashtag_posts(h["tag"], args.limit)
            print(f"  #{h['tag']}: {len(posts)} 条")
            all_posts.extend(posts)
            time.sleep(0.5)
    else:
        for a in accounts:
            print(f"  [{a['priority']}] @{a['handle']} ({a['name']})...")
            posts = fetch_account_posts(a["handle"], a["brand"], args.limit)
            print(f"       → {len(posts)} 条")
            all_posts.extend(posts)
            time.sleep(0.5)

    print(f"\n总计: {len(all_posts)} 条")
    if all_posts:
        out = save_json(all_posts, OUTPUT_DIR)
        print(f"JSON → {out}")
        if args.write_db:
            print(f"DuckDB → {write_to_db(all_posts)} 条")
