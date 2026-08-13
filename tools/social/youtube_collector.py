"""YouTube 采集器（Apify streamers~youtube-scraper）。

采集竞品视频与关键词搜索结果（S2/S3）。
TikHub 的 YouTube 端点在当前 Key 等级下不可用（search 恒返 0），改用 Apify。
品牌匹配与竞品账号从 config/competitor_dictionary.json 读取。
actual_status: LIVE（2026-08-13 实测 searchQueries 返回 Momcozy 视频）。
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

from tools.social.dictionary import get_brand_watchlist, load_dictionary

PROJ = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJ / "data" / "processed" / "social"
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"

APIFY_BASE = "https://api.apify.com/v2"
APIFY_ACTOR = "streamers~youtube-scraper"

SEARCH_KEYWORDS = [
    "breast pump review 2026",
    "wearable breast pump comparison",
    "momcozy review",
    "best breast pump working moms",
    "medela vs willow breast pump",
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


def _parse_int(raw) -> int:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        raw = raw.replace(",", "").strip()
        try:
            if raw.endswith("K"):
                return int(float(raw[:-1]) * 1000)
            if raw.endswith("M"):
                return int(float(raw[:-1]) * 1_000_000)
            return int(raw)
        except (ValueError, AttributeError):
            return 0
    return 0


def _mk_post_id(channel: str, video_id: str) -> str:
    raw = f"youtube|{channel}|{video_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


@dataclass
class YouTubeVideo:
    post_id: str
    platform_code: str = "youtube"
    account_handle: str = ""
    account_type: str = "creator"
    competitor_brand: str = ""
    content_type: str = "video"
    title: str = ""
    body_text: str = ""
    published_at: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    engagement_rate: float = 0.0
    is_viral_flag: bool = False
    brand_mentions: list = field(default_factory=list)
    country_code: str = "US"
    language: str = "en"
    is_processed: bool = False
    video_url: str = ""

    def __post_init__(self) -> None:
        combined = f"{self.title} {self.body_text}".lower()
        self.brand_mentions = [b for b in get_brand_watchlist() if b in combined]
        if self.view_count > 500_000:
            self.is_viral_flag = True

    def to_dict(self) -> dict:
        return asdict(self)


def _parse_item(item: dict) -> YouTubeVideo:
    video_id = item.get("id") or ""
    url = item.get("url") or ""
    if not video_id and "watch?v=" in url:
        video_id = url.split("watch?v=")[-1].split("&")[0]
    channel = item.get("channelName") or item.get("channelUsername") or ""

    return YouTubeVideo(
        post_id=_mk_post_id(channel, video_id),
        account_handle=channel,
        title=(item.get("title") or "")[:300],
        body_text=(item.get("text") or "")[:500],
        published_at=str(item.get("date") or ""),
        view_count=_parse_int(item.get("viewCount") or 0),
        like_count=_parse_int(item.get("likes") or 0),
        comment_count=_parse_int(item.get("commentsCount") or 0),
        video_url=url,
    )


def search_videos(keyword: str, limit: int = 20) -> list[YouTubeVideo]:
    token = _get_apify_token()
    resp = httpx.post(
        f"{APIFY_BASE}/acts/{APIFY_ACTOR}/run-sync-get-dataset-items",
        params={"token": token},
        json={"searchQueries": [keyword], "maxResults": limit},
        timeout=180.0,
    )
    if resp.status_code not in (200, 201):
        print(f"  [WARN] search '{keyword}': HTTP {resp.status_code}", file=sys.stderr)
        return []
    items = resp.json()
    return [_parse_item(it) for it in items if isinstance(it, dict)]


def fetch_competitor_videos(limit_per_brand: int = 10) -> list[YouTubeVideo]:
    d = load_dictionary()
    competitors = d["competitors"]["pump"] + d["competitors"]["feeding_appliance"]
    all_videos: list[YouTubeVideo] = []
    for c in competitors:
        name = c["name"]
        try:
            videos = search_videos(f"{name} review", limit_per_brand)
            print(f"  [{c['priority']}] {name}: {len(videos)} 条")
            all_videos.extend(videos)
            time.sleep(1.0)
        except EnvironmentError as e:
            print(f"  ✗ {e}")
            break
    return all_videos


def write_to_db(videos: list[YouTubeVideo]) -> int:
    if not videos:
        return 0
    try:
        import duckdb
    except ImportError:
        return 0
    con = duckdb.connect(str(DB_PATH))
    inserted = 0
    for v in videos:
        d = v.to_dict()
        try:
            con.execute("""
                INSERT OR IGNORE INTO social_posts
                (post_id, platform_code, account_handle, account_type,
                 competitor_brand, content_type, title, body_text,
                 published_at, fetched_at, view_count, like_count, comment_count,
                 engagement_rate, is_viral_flag, brand_mentions,
                 country_code, language, is_processed)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [
                d["post_id"], d["platform_code"], d["account_handle"], d["account_type"],
                d["competitor_brand"], d["content_type"], d["title"], d["body_text"],
                d["published_at"], d["fetched_at"], d["view_count"], d["like_count"],
                d["comment_count"], d["engagement_rate"], d["is_viral_flag"], d["brand_mentions"],
                d["country_code"], d["language"], d["is_processed"],
            ])
            inserted += 1
        except Exception:
            pass
    con.close()
    return inserted


def save_json(videos: list[YouTubeVideo], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = output_dir / f"youtube_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": ts, "video_count": len(videos),
                   "videos": [v.to_dict() for v in videos]},
                  f, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YouTube Collector via Apify")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--search", default="", help="搜索关键词")
    parser.add_argument("--all-competitors", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        d = load_dictionary()
        competitors = d["competitors"]["pump"] + d["competitors"]["feeding_appliance"]
        print(f"搜索关键词: {len(SEARCH_KEYWORDS)} 个")
        print(f"竞品（来自词典）: {len(competitors)} 个（按品牌名搜索）")
        print(f"API: {APIFY_BASE}/acts/{APIFY_ACTOR}")
        sys.exit(0)

    if not os.environ.get("APIFY_API_KEY"):
        print("⚠ APIFY_API_KEY 未设置")
        sys.exit(0)

    videos: list[YouTubeVideo] = []
    if args.search:
        videos = search_videos(args.search, args.limit)
        print(f"搜索 '{args.search}': {len(videos)} 条")
    else:
        for kw in SEARCH_KEYWORDS:
            vids = search_videos(kw, args.limit)
            print(f"  '{kw}': {len(vids)} 条")
            videos.extend(vids)
            time.sleep(1.0)

    print(f"\n总计: {len(videos)} 条, 高互动: {sum(1 for v in videos if v.is_viral_flag)}")
    if videos:
        out = save_json(videos, OUTPUT_DIR)
        print(f"JSON → {out}")
        if args.write_db:
            print(f"DuckDB → {write_to_db(videos)} 条")
