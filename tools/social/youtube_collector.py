"""
tools/social/youtube_collector.py — YouTube 内容采集器（TikHub API）

是什么：通过 TikHub API 采集 YouTube 竞品频道视频和关键词搜索结果
       TikHub YouTube API 无需 Google Cloud 配额，按次付费 $0.001/请求
       channel_id 参数直接传 @handle，无需先查 UCxxxx channel ID

API 端点：
  GET https://api.tikhub.io/api/v1/youtube/web/get_channel_videos_v2
    ?channel_id=@willowpump&sortBy=newest&contentType=videos
  GET https://api.tikhub.io/api/v1/youtube/web/search_video
    ?keyword=breast+pump+review
  认证：Authorization: Bearer {TIKHUB_API_KEY}（与 TikTok 共用同一 Key）

actual_status: CODE_UNVERIFIED（需在部署服务器配置 TIKHUB_API_KEY 后验证）

快速测试：
    python3 tools/social/youtube_collector.py --dry-run
    python3 tools/social/youtube_collector.py --channel @willowpump --limit 5
"""
from __future__ import annotations

import hashlib
import json
import os

import re as _re
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
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))

PROJ = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJ / "data" / "processed" / "social"
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"

TIKHUB_BASE = "https://api.tikhub.io"

COMPETITOR_CHANNELS = [
    # P0 — 吸奶器直接竞品（channel_id 已验证）
    {"brand": "eufy",        "handle": "@eufybaby",           "channel_id": "UC5TlekIUP9KxCD_aawBt_qA", "priority": "P0"},
    {"brand": "elvie",       "handle": "@elvie",              "channel_id": "UCWoUFX2elO3DE09cdP4Y78Q", "priority": "P0"},
    {"brand": "willow",      "handle": "@willowpump",         "channel_id": "UChgIEtG70rxzz-2mkR64Myg", "priority": "P0"},
    {"brand": "spectra",     "handle": "@spectrababyusa",     "channel_id": "UCi0oDMjpc__Urp5kkRClgAg", "priority": "P0"},
    {"brand": "medela",      "handle": "@medelaofficial",     "channel_id": "UC9PwVbd1UyoS0R8CfslBsOg", "priority": "P0"},
    {"brand": "frida",       "handle": "@fridababy",          "channel_id": "UC-4k2uKsl1n23l6XlIQoCdw", "priority": "P1"},
    # P1 — 喂养电器竞品
    {"brand": "baby_brezza", "handle": "@babybrezza",         "channel_id": "UCFkaJtu9iB1phvZl3a6QR8g", "priority": "P0"},
    # P1 — 其他（channel_id 部分验证）
    {"brand": "lansinoh",    "handle": "@lansinoh",           "channel_id": "UC28FG6ilFF0ehzgzwyEv_lg", "priority": "P1"},
    {"brand": "nanit",       "handle": "@nanit",              "channel_id": "UCzunQh6jG5aWP51-lMsvtxQ", "priority": "P1"},
    {"brand": "haakaa",      "handle": "@haakaanz",           "channel_id": "UChp8nMco_CXCcrLe_vsSZMg", "priority": "P2"},
]

SEARCH_KEYWORDS = [
    "breast pump review 2026",
    "wearable breast pump comparison",
    "momcozy review",
    "best breast pump working moms",
    "medela vs willow breast pump",
]

BRAND_WATCHLIST = [
    "momcozy", "medela", "willow", "elvie", "spectra", "lansinoh",
    "babybuddha", "nanit", "owlet", "hatch", "breast pump",
    "wearable pump", "hands free pump", "kleanpal",
]


def _get_headers() -> dict:
    api_key = os.environ.get("TIKHUB_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "TIKHUB_API_KEY not set.\n"
            "  获取：https://user.tikhub.io/dashboard/api-marketplace\n"
            "  设置：export TIKHUB_API_KEY=\'your-key\'"
        )
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _mk_post_id(handle: str, video_id: str) -> str:
    raw = f"youtube|{handle}|{video_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


def _parse_count(raw) -> int:
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


@dataclass
class YouTubeVideo:
    post_id: str
    platform_code: str = "youtube"
    account_handle: str = ""
    account_type: str = "competitor"
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
        self.brand_mentions = [b for b in BRAND_WATCHLIST if b in combined]
        if self.view_count > 500_000:
            self.is_viral_flag = True

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_channel_videos(handle: str, brand: str, limit: int = 20) -> list:
    url = f"{TIKHUB_BASE}/api/v1/youtube/web/get_channel_videos_v2"
    params = {"channel_id": handle, "sortBy": "newest", "contentType": "videos", "lang": "en-US"}
    videos = []
    fetched = 0
    next_token = None

    try:
        while fetched < limit:
            if next_token:
                params["nextToken"] = next_token
            resp = httpx.get(url, headers=_get_headers(), params=params, timeout=20.0)
            if resp.status_code == 401:
                raise EnvironmentError("TIKHUB_API_KEY 无效（401）")
            if resp.status_code != 200:
                print(f"  [WARN] {handle}: HTTP {resp.status_code}", file=sys.stderr)
                break

            data = resp.json()
            items = (data.get("data") or {}).get("videos") or []
            if not items:
                break

            for item in items:
                vid_id = item.get("videoId") or item.get("id") or ""
                if not vid_id:
                    continue
                post_id = _mk_post_id(handle, vid_id)
                videos.append(YouTubeVideo(
                    post_id=post_id,
                    account_handle=handle,
                    competitor_brand=brand,
                    title=(item.get("title") or "")[:300],
                    body_text=(item.get("description") or "")[:500],
                    published_at=str(item.get("publishedAt") or ""),
                    view_count=_parse_count(item.get("viewCount") or 0),
                    like_count=_parse_count(item.get("likeCount") or 0),
                    comment_count=_parse_count(item.get("commentCount") or 0),
                    video_url=f"https://www.youtube.com/watch?v={vid_id}",
                ))
                fetched += 1
                if fetched >= limit:
                    break

            next_token = (data.get("data") or {}).get("nextToken") or None
            if not next_token:
                break
            time.sleep(0.3)

    except EnvironmentError:
        raise
    except Exception as exc:
        print(f"  [ERROR] fetch_channel_videos({handle}): {exc}", file=sys.stderr)

    return videos


def search_videos(keyword: str, limit: int = 10) -> list:
    url = f"{TIKHUB_BASE}/api/v1/youtube/web/search_video"
    params = {"keyword": keyword, "lang": "en-US"}
    videos = []
    try:
        resp = httpx.get(url, headers=_get_headers(), params=params, timeout=20.0)
        if resp.status_code != 200:
            return []
        data = resp.json()
        items = (data.get("data") or {}).get("videos") or []
        for item in items[:limit]:
            vid_id = item.get("videoId") or item.get("id") or ""
            handle = item.get("channelTitle") or ""
            post_id = _mk_post_id(handle, vid_id)
            videos.append(YouTubeVideo(
                post_id=post_id,
                account_handle=handle,
                account_type="creator",
                title=(item.get("title") or "")[:300],
                body_text=(item.get("description") or "")[:300],
                published_at=str(item.get("publishedAt") or ""),
                view_count=_parse_count(item.get("viewCount") or 0),
                video_url=f"https://www.youtube.com/watch?v={vid_id}",
            ))
    except EnvironmentError:
        raise
    except Exception as exc:
        print(f"  [ERROR] search_videos({keyword}): {exc}", file=sys.stderr)
    return videos


def write_to_db(videos: list) -> int:
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


def save_json(videos: list, output_dir: Path) -> Path:
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
    parser = argparse.ArgumentParser(description="YouTube Collector via TikHub API")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--channel", default="", help="@handle，如 @willowpump")
    parser.add_argument("--search", default="", help="搜索关键词")
    parser.add_argument("--all-competitors", action="store_true")
    parser.add_argument("--priority", default="P0", choices=["P0", "P1"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("YouTube 竞品频道配置（TikHub API）:")
        for ch in COMPETITOR_CHANNELS:
            print(f"  [{ch['priority']}] {ch['brand']:12} → {ch['handle']}")
        print(f"\nAPI: {TIKHUB_BASE}/api/v1/youtube/web/get_channel_videos_v2")
        print("认证: Bearer $TIKHUB_API_KEY（与 TikTok 共用）")
        sys.exit(0)

    if not os.environ.get("TIKHUB_API_KEY"):
        print("⚠ TIKHUB_API_KEY 未设置")
        print("  获取：https://user.tikhub.io/dashboard/api-marketplace")
        sys.exit(0)

    videos = []
    if args.search:
        print(f"搜索: {args.search}")
        videos = search_videos(args.search, args.limit)
        print(f"  → {len(videos)} 条")
    elif args.channel:
        handle = args.channel if args.channel.startswith("@") else f"@{args.channel}"
        brand = next((c["brand"] for c in COMPETITOR_CHANNELS if c["handle"] == handle), "unknown")
        print(f"采集: {handle} ({brand})")
        videos = fetch_channel_videos(handle, brand, args.limit)
        print(f"  → {len(videos)} 条")
    else:
        run_p1 = args.all_competitors or args.priority == "P1"
        for ch in COMPETITOR_CHANNELS:
            if ch["priority"] == "P1" and not run_p1:
                continue
            print(f"  [{ch['priority']}] {ch['brand']} ({ch['handle']})...")
            vids = fetch_channel_videos(ch["handle"], ch["brand"], args.limit)
            viral = sum(1 for v in vids if v.is_viral_flag)
            print(f"       → {len(vids)} 条, 高互动 {viral}")
            videos.extend(vids)
            time.sleep(0.5)

    print(f"\n总计: {len(videos)} 条, 高互动: {sum(1 for v in videos if v.is_viral_flag)}")
    if videos:
        out = save_json(videos, OUTPUT_DIR)
        print(f"JSON → {out}")
        if args.write_db:
            inserted = write_to_db(videos)
            print(f"DuckDB → {inserted} 条")
