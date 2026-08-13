"""
tools/social/tiktok_collector.py — TikTok 内容采集器（TikHub API）

是什么：通过 TikHub API 采集 TikTok 竞品账号内容、用户讨论、趋势数据
输入：竞品账号列表 + 关键词列表（来自 dim_competitor_social_accounts）
输出：写入 DuckDB social_posts + social_trends 表
不是什么：不做 LLM 分析，不做情感评分（下游处理）

TikHub API 文档：https://tikhub.io
认证：Bearer Token，在 https://tikhub.io 注册获取
环境变量：export TIKHUB_API_KEY="your-key"

actual_status: CODE_UNVERIFIED（本机无法测试网络，需在部署服务器验证）

快速测试：
    python3 tools/social/tiktok_collector.py --dry-run
    python3 tools/social/tiktok_collector.py --account @willowpump --limit 10
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

sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))

PROJ = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJ / "data" / "processed" / "social"
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"

TIKHUB_BASE = "https://api.tikhub.io"

# ── 竞品账号配置（来自 dim_competitor_social_accounts）──────────
# 竞品账号配置 v1.0（2026-08-12 业务确认）
# 来源：docs/竞品维度表v1.0.md
COMPETITOR_ACCOUNTS = [
    # ── 吸奶器 T1 直接竞品（P0）──────────────────────────────
    {"brand": "eufy",         "handle": "eufybaby",          "product_line": "pump",             "priority": "P0"},
    {"brand": "elvie",        "handle": "elvieofficial",     "product_line": "pump",             "priority": "P0"},
    {"brand": "willow",       "handle": "willowpump",        "product_line": "pump",             "priority": "P0"},
    {"brand": "spectra",      "handle": "spectrababyusa",    "product_line": "pump",             "priority": "P0"},
    {"brand": "medela",       "handle": "medela_official",   "product_line": "pump",             "priority": "P0"},
    # ── 吸奶器 T2 核心竞品（P1）──────────────────────────────
    {"brand": "frida",        "handle": "fridamom",          "product_line": "pump",             "priority": "P1"},
    {"brand": "philips_avent","handle": "philipsavent",      "product_line": "pump_feeding",     "priority": "P1"},
    {"brand": "motif_medical","handle": "motifmedical",      "product_line": "pump",             "priority": "P1"},
    {"brand": "haakaa",       "handle": "haakaanz",          "product_line": "pump",             "priority": "P1"},
    # ── 吸奶器 T2 保留监测（P2，当前无内容但账号存在）──────────
    {"brand": "lansinoh",     "handle": "lansinoh",          "product_line": "pump",             "priority": "P2"},
    {"brand": "babybuddha",   "handle": "babybuddhaofficial","product_line": "pump",             "priority": "P2"},
    # ── 喂养电器 T1 直接竞品（P0）──────────────────────────────
    {"brand": "baby_brezza",  "handle": "babybrezza",        "product_line": "feeding_appliance","priority": "P0"},
    {"brand": "grownsy",      "handle": "grownsy",           "product_line": "feeding_appliance","priority": "P0"},
    # ── 喂养电器 T2（P1）──────────────────────────────────────
    {"brand": "dr_browns",    "handle": "drbrowns",          "product_line": "feeding_appliance","priority": "P1"},
]

# ── 母婴关键词（用于搜索和话题发现）──────────────────────────────
BABY_KEYWORDS = [
    "breast pump", "wearable pump", "momcozy", "medela", "willow pump",
    "elvie pump", "hands free pump", "breastfeeding", "pumping mom",
    "baby bottle sterilizer", "kleanpal", "baby monitor",
]


@dataclass
class TikTokPost:
    post_id: str
    platform_code: str = "tiktok"
    account_handle: str = ""
    account_type: str = "competitor"
    competitor_brand: str = ""
    content_type: str = "video"
    title: str = ""
    body_text: str = ""
    hashtags: list = field(default_factory=list)
    bgm_title: str = ""
    bgm_author: str = ""
    published_at: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    engagement_rate: float = 0.0
    view_velocity_24h: int = 0
    is_viral_flag: bool = False
    brand_mentions: list = field(default_factory=list)
    is_paid_collab: bool = False
    country_code: str = "US"
    language: str = "en"
    is_processed: bool = False

    BRAND_WATCHLIST: list = field(
        default_factory=lambda: [
            "momcozy", "medela", "willow", "elvie", "spectra",
            "lansinoh", "nanit", "owlet", "hatch", "babybuddha",
        ],
        repr=False,
    )

    def __post_init__(self) -> None:
        combined = f"{self.body_text} {' '.join(self.hashtags)}".lower()
        self.brand_mentions = [b for b in self.BRAND_WATCHLIST if b in combined]
        if self.like_count + self.comment_count + self.share_count > 0:
            total_followers = 100000
            self.engagement_rate = round(
                (self.like_count + self.comment_count + self.share_count) / total_followers, 4
            )

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("BRAND_WATCHLIST", None)
        return d


def _mk_post_id(platform: str, handle: str, native_id: str) -> str:
    raw = f"{platform}|{handle}|{native_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


def _get_headers() -> dict:
    api_key = os.environ.get("TIKHUB_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "TIKHUB_API_KEY not set. "
            "Get your key at https://tikhub.io, then: export TIKHUB_API_KEY='your-key'"
        )
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def fetch_account_videos(handle: str, limit: int = 20) -> list[dict]:
    """获取指定账号的最新视频列表"""
    import httpx

    url = f"{TIKHUB_BASE}/api/v1/tiktok/web/user/posts"
    params = {
        "unique_id": handle.lstrip("@"),
        "count": min(limit, 35),
    }
    try:
        resp = httpx.get(url, headers=_get_headers(), params=params, timeout=20.0)
        if resp.status_code == 200:
            data = resp.json()
            return (data.get("data") or {}).get("itemList") or []
        elif resp.status_code == 401:
            raise EnvironmentError(f"TikHub API Key 无效或已过期（401）")
        else:
            print(f"  [WARN] {handle}: HTTP {resp.status_code}", file=sys.stderr)
            return []
    except Exception as exc:
        print(f"  [ERROR] fetch_account_videos({handle}): {exc}", file=sys.stderr)
        return []


def parse_video_item(item: dict, brand: str, handle: str) -> TikTokPost:
    stats = item.get("stats") or {}
    music = item.get("music") or {}
    desc = item.get("desc") or ""
    challenges = item.get("challenges") or []
    hashtags = [f"#{c.get('title','')}" for c in challenges if c.get("title")]

    create_ts = item.get("createTime") or 0
    published_at = datetime.fromtimestamp(create_ts, tz=timezone.utc).isoformat() if create_ts else ""

    view_count = stats.get("playCount") or 0
    like_count = stats.get("diggCount") or 0
    comment_count = stats.get("commentCount") or 0
    share_count = stats.get("shareCount") or 0

    native_id = item.get("id") or item.get("aweme_id") or desc[:20]
    post_id = _mk_post_id("tiktok", handle, str(native_id))

    ad_labels = [label.get("text", "").lower() for label in item.get("adAuthorization", []) or []]
    is_paid = any("ad" in l or "sponsor" in l or "paid" in l for l in ad_labels)

    return TikTokPost(
        post_id=post_id,
        account_handle=handle,
        competitor_brand=brand,
        body_text=desc[:500],
        hashtags=hashtags[:20],
        bgm_title=music.get("title") or "",
        bgm_author=music.get("authorName") or "",
        published_at=published_at,
        view_count=view_count,
        like_count=like_count,
        comment_count=comment_count,
        share_count=share_count,
        is_viral_flag=(view_count > 1_000_000),
        is_paid_collab=is_paid,
    )


def fetch_trending(region: str = "US", limit: int = 20) -> list[dict]:
    """获取 TikTok 区域热门内容"""
    import httpx
    url = f"{TIKHUB_BASE}/api/v1/tiktok/web/explore/trending"
    params = {"region": region, "count": limit}
    try:
        resp = httpx.get(url, headers=_get_headers(), params=params, timeout=20.0)
        if resp.status_code == 200:
            return (resp.json().get("data") or {}).get("itemList") or []
        return []
    except Exception as exc:
        print(f"  [ERROR] fetch_trending: {exc}", file=sys.stderr)
        return []


def fetch_hashtag_videos(hashtag: str, limit: int = 20) -> list[dict]:
    """获取指定 Hashtag 下的视频"""
    import httpx
    url = f"{TIKHUB_BASE}/api/v1/tiktok/web/hashtag/videos"
    params = {"keywords": hashtag.lstrip("#"), "count": limit}
    try:
        resp = httpx.get(url, headers=_get_headers(), params=params, timeout=20.0)
        if resp.status_code == 200:
            return (resp.json().get("data") or {}).get("itemList") or []
        return []
    except Exception as exc:
        print(f"  [ERROR] fetch_hashtag({hashtag}): {exc}", file=sys.stderr)
        return []


def write_to_db(posts: list[TikTokPost]) -> int:
    if not posts:
        return 0
    try:
        import duckdb
    except ImportError:
        print("[ERROR] duckdb not available")
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
                 bgm_title, bgm_author, published_at, fetched_at,
                 view_count, like_count, comment_count, share_count,
                 engagement_rate, is_viral_flag, brand_mentions, is_paid_collab,
                 country_code, language, is_processed)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [
                d["post_id"], d["platform_code"], d["account_handle"], d["account_type"],
                d["competitor_brand"], d["content_type"], d["body_text"], d["hashtags"],
                d["bgm_title"], d["bgm_author"], d["published_at"], d["fetched_at"],
                d["view_count"], d["like_count"], d["comment_count"], d["share_count"],
                d["engagement_rate"], d["is_viral_flag"], d["brand_mentions"], d["is_paid_collab"],
                d["country_code"], d["language"], d["is_processed"],
            ])
            inserted += 1
        except Exception:
            pass
    con.close()
    return inserted


def save_json(posts: list[TikTokPost], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = output_dir / f"tiktok_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {"fetched_at": ts, "post_count": len(posts),
             "posts": [p.to_dict() for p in posts]},
            f, ensure_ascii=False, indent=2,
        )
    return out


def run_competitor_sweep(limit_per_account: int = 20, dry_run: bool = False) -> list[TikTokPost]:
    all_posts = []
    for acct in COMPETITOR_ACCOUNTS:
        handle = acct["handle"]
        brand = acct["brand"]
        print(f"  [{acct['priority']}] @{handle} ({brand})...")
        items = fetch_account_videos(handle, limit=limit_per_account)
        posts = [parse_video_item(item, brand, handle) for item in items]
        viral_count = sum(1 for p in posts if p.is_viral_flag)
        print(f"       → {len(posts)} 条, 高互动 {viral_count}")
        all_posts.extend(posts)
        time.sleep(0.5)
    return all_posts


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TikTok Competitor Content Collector")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--account", default="", help="单个账号 handle（如 @willowpump）")
    parser.add_argument("--hashtag", default="", help="单个 Hashtag（如 breastpump）")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("TIKHUB_API_KEY"):
        print("⚠ TIKHUB_API_KEY 未设置")
        print("  获取：https://tikhub.io → 注册账号 → API Keys")
        print("  设置：export TIKHUB_API_KEY='your-key'")
        print("  验证：python3 tools/social/tiktok_collector.py --dry-run")
        sys.exit(0)

    if args.dry_run:
        print(f"[dry-run] 竞品账号: {len(COMPETITOR_ACCOUNTS)} 个")
        for a in COMPETITOR_ACCOUNTS:
            print(f"  [{a['priority']}] @{a['handle']} ({a['brand']})")
        sys.exit(0)

    posts = []
    if args.account:
        handle = args.account.lstrip("@")
        items = fetch_account_videos(handle, args.limit)
        brand = next((a["brand"] for a in COMPETITOR_ACCOUNTS if a["handle"] == handle), "unknown")
        posts = [parse_video_item(i, brand, handle) for i in items]
    elif args.hashtag:
        items = fetch_hashtag_videos(args.hashtag, args.limit)
        posts = [parse_video_item(i, "user", args.hashtag) for i in items]
    else:
        posts = run_competitor_sweep(limit_per_account=args.limit)

    print(f"\n总计: {len(posts)} 条, 高互动: {sum(1 for p in posts if p.is_viral_flag)}")

    out = save_json(posts, OUTPUT_DIR)
    print(f"JSON → {out}")

    if args.write_db:
        inserted = write_to_db(posts)
        print(f"DuckDB → {inserted} 条")
