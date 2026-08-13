"""
tools/social/keyword_search_collector.py — 关键词搜索采集器

是什么：
  通过品牌词/品类词/商品词在 TikTok + Instagram + YouTube 搜索，
  发现提及竞品的内容创作者，自动识别是否付费合作，
  写入 dim_competitor_kol_collabs + dim_creator_profiles

核心逻辑：
  搜索关键词 → 获取视频/帖子 → 提取创作者 → 检测 #ad/#sponsored
  → 写入 collab 表 → 反向补充 KOL 档案

三类关键词：
  brand_keywords:   品牌词（momcozy / eufy S1 Pro）—— 精准发现
  category_keywords: 品类词（wearable breast pump review）—— 发现潜力 KOL
  product_keywords: 商品词（momcozy M5 review / kleanpal review）—— 发现测评内容

actual_status: CODE_UNVERIFIED（需在部署服务器验证）

快速测试：
    python3 tools/social/keyword_search_collector.py --dry-run
    python3 tools/social/keyword_search_collector.py --type brand --platform tiktok --limit 10
    python3 tools/social/keyword_search_collector.py --keyword "eufy S1 Pro review" --platform tiktok
"""
from __future__ import annotations

import hashlib
import json
import os
import re as _re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

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

# ── 三类关键词配置 ───────────────────────────────────────────
SEARCH_KEYWORDS = {

    # 1. 品牌词 — 精准发现竞品相关内容
    "brand": [
        # Momcozy 自有品牌（监测自身被提及）
        {"kw": "momcozy",            "brand": "momcozy",    "type": "brand"},
        {"kw": "momcozy review",     "brand": "momcozy",    "type": "brand"},
        {"kw": "kleanpal",           "brand": "momcozy",    "type": "brand"},
        # T1 直接竞品
        {"kw": "eufy S1 Pro",        "brand": "eufy",       "type": "brand"},
        {"kw": "eufy breast pump",   "brand": "eufy",       "type": "brand"},
        {"kw": "elvie pump",         "brand": "elvie",      "type": "brand"},
        {"kw": "willow go pump",     "brand": "willow",     "type": "brand"},
        {"kw": "willow 360",         "brand": "willow",     "type": "brand"},
        {"kw": "spectra S1",         "brand": "spectra",    "type": "brand"},
        {"kw": "spectra S2",         "brand": "spectra",    "type": "brand"},
        # T2 传统竞品
        {"kw": "medela pump",        "brand": "medela",     "type": "brand"},
        {"kw": "baby brezza sterilizer","brand": "baby_brezza","type":"brand"},
        {"kw": "grownsy sterilizer", "brand": "grownsy",    "type": "brand"},
        {"kw": "frida breast pump",  "brand": "frida",      "type": "brand"},
    ],

    # 2. 品类词 — 发现品类 KOL（不限品牌）
    "category": [
        {"kw": "wearable breast pump review",    "brand": None, "type": "category"},
        {"kw": "best breast pump 2026",          "brand": None, "type": "category"},
        {"kw": "breast pump comparison",         "brand": None, "type": "category"},
        {"kw": "hands free pump review",         "brand": None, "type": "category"},
        {"kw": "bottle sterilizer review",       "brand": None, "type": "category"},
        {"kw": "pumping mom tips",               "brand": None, "type": "category"},
        {"kw": "exclusively pumping tips",       "brand": None, "type": "category"},
        {"kw": "back to work pumping",           "brand": None, "type": "category"},
        {"kw": "breast pump insurance",          "brand": None, "type": "category"},
        {"kw": "wearable pump output",           "brand": None, "type": "category"},
    ],

    # 3. 商品词 — 精准测评发现
    "product": [
        {"kw": "momcozy M5 review",             "brand": "momcozy",  "type": "product"},
        {"kw": "momcozy V1 Pro review",         "brand": "momcozy",  "type": "product"},
        {"kw": "momcozy Air 1 review",          "brand": "momcozy",  "type": "product"},
        {"kw": "momcozy W1 review",             "brand": "momcozy",  "type": "product"},
        {"kw": "eufy S1 Pro vs momcozy",        "brand": "eufy",     "type": "product"},
        {"kw": "elvie vs willow",               "brand": "elvie",    "type": "product"},
        {"kw": "spectra S1 vs S2",              "brand": "spectra",  "type": "product"},
        {"kw": "kleanpal review",               "brand": "momcozy",  "type": "product"},
        {"kw": "kleanpal vs baby brezza",       "brand": "momcozy",  "type": "product"},
        {"kw": "motif luna review",             "brand": "motif",    "type": "product"},
        {"kw": "lansinoh discreetduo review",   "brand": "lansinoh", "type": "product"},
        {"kw": "zomee Z2 review",               "brand": "zomee",    "type": "product"},
    ],
}

# 付费合作标识词
PAID_COLLAB_SIGNALS = [
    "#ad", "#sponsored", "#gifted", "#partner", "#paidpartnership",
    "#collabwith", "#brandambassador", "paid partnership", "gifted by",
    "c/o", "use code", "discount code", "link in bio", "#momcozypartner",
]

# 内容形式识别
CONTENT_FORMAT_SIGNALS = {
    "review": ["review", "honest review", "worth it", "my thoughts", "tested"],
    "comparison": ["vs", "versus", "or", "comparison", "which is better"],
    "tutorial": ["how to", "setup", "tips", "guide", "tutorial"],
    "unboxing": ["unboxing", "first look", "just got"],
    "lifestyle": ["daily routine", "mom life", "pumping journey", "postpartum"],
}

BRAND_WATCHLIST = [
    "momcozy", "eufy", "elvie", "willow", "spectra", "medela",
    "frida", "baby brezza", "kleanpal", "lansinoh", "grownsy",
    "motif", "babybuddha", "haakaa", "wabi baby",
]


def _get_headers() -> dict:
    key = os.environ.get("TIKHUB_API_KEY", "")
    if not key:
        raise EnvironmentError("TIKHUB_API_KEY not set")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _mk_collab_id(platform: str, post_id: str) -> str:
    raw = f"collab|{platform}|{post_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


def _mk_creator_id(platform: str, handle: str) -> str:
    return f"{platform}_{handle.lstrip('@').lower()}"


def _detect_paid_collab(text: str) -> tuple:
    """返回 (is_paid, evidence_string)"""
    text_lower = text.lower()
    for signal in PAID_COLLAB_SIGNALS:
        if signal.lower() in text_lower:
            return True, signal
    return False, ""


def _detect_content_format(text: str) -> str:
    text_lower = text.lower()
    for fmt, signals in CONTENT_FORMAT_SIGNALS.items():
        if any(s in text_lower for s in signals):
            return fmt
    return "other"


def _detect_content_theme(text: str, hashtags: list) -> str:
    combined = f"{text} {' '.join(hashtags)}".lower()
    themes = {
        "comfort": ["comfort", "pain free", "heat", "warming", "soft"],
        "output": ["output", "milk supply", "ounces", "production", "yield"],
        "convenience": ["hands free", "wireless", "portable", "discreet", "quiet"],
        "price_value": ["affordable", "budget", "cheap", "price", "value", "worth it"],
        "insurance": ["insurance", "covered", "medicaid", "fsa", "hsa"],
        "comparison": ["vs", "versus", "better than", "compared to"],
        "safety": ["safe", "bpa", "material", "recall", "defect"],
    }
    for theme, kws in themes.items():
        if any(k in combined for k in kws):
            return theme
    return "general"


def _extract_products_mentioned(text: str) -> list:
    """从文本中提取具体型号"""
    text_lower = text.lower()
    PRODUCT_PATTERNS = [
        r'\bmomcozy\s+[msvaw]\d+\b',     # momcozy M5, S12, V1, Air 1, W1
        r'\beufy\s+s1\s*pro\b',
        r'\beufy\s+e10\b',
        r'\bwillow\s+go\b',
        r'\bwillow\s+360\b',
        r'\belvie\s+pump\b',
        r'\belvie\s+stride\b',
        r'\bspectra\s+s[12]\b',
        r'\bspectra\s+9\b',
        r'\bkleanpal\s+pro?\b',
        r'\bmedela\s+\w+\s*\w*\b',
        r'\bbabybuddha\s+2\.0\b',
    ]
    found = []
    for pattern in PRODUCT_PATTERNS:
        matches = _re.findall(pattern, text_lower)
        found.extend(matches)
    return list(set(found))


@dataclass
class CollabRecord:
    collab_id: str
    competitor_brand: str
    creator_id: str
    platform_code: str
    post_id: str
    post_url: str
    post_title: str
    post_body: str
    hashtags: list
    published_at: str
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_paid_collab: bool = False
    collab_type: str = "organic"
    collab_evidence: str = ""
    content_theme: str = ""
    content_format: str = ""
    product_mentioned: list = field(default_factory=list)
    competitor_angle: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    engagement_rate: float = 0.0
    view_velocity_7d: int = 0
    is_viral: bool = False
    is_repeat_collab: bool = False
    collab_sequence_num: int = 1
    discovery_method: str = "keyword_search"
    search_keyword: str = ""
    verified: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def search_tiktok(keyword: str, limit: int = 20) -> list:
    """TikTok 关键词搜索，返回视频列表"""
    resp = httpx.get(
        f"{TIKHUB_BASE}/api/v1/tiktok/app/v3/fetch_creator_search_insights_videos",
        headers=_get_headers(),
        params={"keyword": keyword, "count": limit},
        timeout=15.0,
    )
    if resp.status_code != 200:
        # fallback 到 web search
        resp = httpx.get(
            f"{TIKHUB_BASE}/api/v1/tiktok/web/fetch_search_video",
            headers=_get_headers(),
            params={"keyword": keyword, "count": limit},
            timeout=15.0,
        )
    if resp.status_code != 200:
        return []
    data = resp.json()
    return (data.get("data") or {}).get("aweme_list") or []


def search_instagram(keyword: str, limit: int = 20) -> list:
    """Instagram 关键词搜索 Reels"""
    resp = httpx.get(
        f"{TIKHUB_BASE}/api/v1/instagram/web/search_reels",
        headers=_get_headers(),
        params={"keyword": keyword, "count": limit},
        timeout=15.0,
    )
    if resp.status_code != 200:
        return []
    return (resp.json().get("data") or {}).get("items") or []


def search_youtube(keyword: str, limit: int = 10) -> list:
    """YouTube 关键词搜索视频"""
    resp = httpx.get(
        f"{TIKHUB_BASE}/api/v1/youtube/web/search_video",
        headers=_get_headers(),
        params={"search_query": keyword, "language_code": "en"},
        timeout=15.0,
    )
    if resp.status_code != 200:
        return []
    return (resp.json().get("data") or {}).get("videos") or []


def _parse_tiktok_video(video: dict, kw_config: dict) -> Optional[CollabRecord]:
    """从 TikTok 视频解析 CollabRecord"""
    stats = video.get("statistics") or {}
    author = video.get("author") or {}
    desc = video.get("desc") or ""
    cha_list = video.get("cha_list") or []
    hashtags = [f"#{c.get('cha_name','')}" for c in cha_list if c.get("cha_name")]

    is_paid, evidence = _detect_paid_collab(desc + " " + " ".join(hashtags))
    brand = kw_config.get("brand")
    if not brand:
        # 品类词搜索，从内容里找品牌
        combined = f"{desc} {' '.join(hashtags)}".lower()
        brand_found = [b for b in BRAND_WATCHLIST if b in combined]
        brand = brand_found[0] if brand_found else "unknown"

    aweme_id = video.get("aweme_id") or video.get("id") or ""
    handle = author.get("unique_id") or ""
    view_count = stats.get("play_count") or 0
    like_count = stats.get("digg_count") or 0
    comment_count = stats.get("comment_count") or 0
    create_ts = video.get("create_time") or 0
    published = (datetime.fromtimestamp(int(create_ts), tz=timezone.utc).isoformat()
                 if create_ts else "")

    return CollabRecord(
        collab_id=_mk_collab_id("tiktok", str(aweme_id)),
        competitor_brand=brand,
        creator_id=_mk_creator_id("tiktok", handle),
        platform_code="tiktok",
        post_id=str(aweme_id),
        post_url=f"https://www.tiktok.com/@{handle}/video/{aweme_id}",
        post_title="",
        post_body=desc[:500],
        hashtags=hashtags[:20],
        published_at=published,
        is_paid_collab=is_paid,
        collab_type="paid" if is_paid else "organic",
        collab_evidence=evidence,
        content_theme=_detect_content_theme(desc, hashtags),
        content_format=_detect_content_format(desc),
        product_mentioned=_extract_products_mentioned(desc),
        view_count=view_count,
        like_count=like_count,
        comment_count=comment_count,
        is_viral=view_count > 500000,
        discovery_method="keyword_search",
        search_keyword=kw_config.get("kw", ""),
    )


def _parse_youtube_video(video: dict, kw_config: dict) -> Optional[CollabRecord]:
    vid_id = video.get("videoId") or video.get("id") or ""
    title = (video.get("title") or "")[:300]
    desc = (video.get("description") or "")[:500]
    channel = video.get("channelTitle") or video.get("author") or ""
    view_count = int(str(video.get("viewCount") or "0").replace(",",""))
    published = str(video.get("publishedAt") or "")

    combined = f"{title} {desc}"
    is_paid, evidence = _detect_paid_collab(combined)
    brand = kw_config.get("brand")
    if not brand:
        brand_found = [b for b in BRAND_WATCHLIST if b in combined.lower()]
        brand = brand_found[0] if brand_found else "unknown"

    return CollabRecord(
        collab_id=_mk_collab_id("youtube", str(vid_id)),
        competitor_brand=brand,
        creator_id=_mk_creator_id("youtube", channel),
        platform_code="youtube",
        post_id=str(vid_id),
        post_url=f"https://www.youtube.com/watch?v={vid_id}",
        post_title=title,
        post_body=desc,
        hashtags=[],
        published_at=published,
        is_paid_collab=is_paid,
        collab_type="paid" if is_paid else "organic",
        collab_evidence=evidence,
        content_theme=_detect_content_theme(combined, []),
        content_format=_detect_content_format(combined),
        product_mentioned=_extract_products_mentioned(combined),
        view_count=view_count,
        is_viral=view_count > 100000,
        discovery_method="keyword_search",
        search_keyword=kw_config.get("kw", ""),
    )


def run_keyword_search(kw_types: list, platforms: list, limit: int = 20) -> list:
    """主搜索函数：三类词 × 三平台"""
    all_records = []
    seen_ids = set()

    for kw_type in kw_types:
        keywords = SEARCH_KEYWORDS.get(kw_type, [])
        for kw_config in keywords:
            kw = kw_config["kw"]
            for platform in platforms:
                print(f"  [{kw_type}] [{platform}] '{kw}'...")
                try:
                    if platform == "tiktok":
                        videos = search_tiktok(kw, limit)
                        for v in videos:
                            r = _parse_tiktok_video(v, kw_config)
                            if r and r.collab_id not in seen_ids:
                                seen_ids.add(r.collab_id)
                                all_records.append(r)

                    elif platform == "youtube":
                        videos = search_youtube(kw, limit // 2)
                        for v in videos:
                            r = _parse_youtube_video(v, kw_config)
                            if r and r.collab_id not in seen_ids:
                                seen_ids.add(r.collab_id)
                                all_records.append(r)

                    elif platform == "instagram":
                        # Instagram Hashtag 搜索
                        from tools.social.instagram_collector import fetch_hashtag_posts
                        posts = fetch_hashtag_posts(kw.replace(" ", ""), limit)
                        for p in posts:
                            cid = _mk_collab_id("instagram", p.post_id)
                            if cid in seen_ids:
                                continue
                            seen_ids.add(cid)
                            brand = kw_config.get("brand")
                            if not brand:
                                brand_found = [b for b in BRAND_WATCHLIST
                                               if b in p.body_text.lower()]
                                brand = brand_found[0] if brand_found else "unknown"
                            combined = p.body_text
                            is_paid, evidence = _detect_paid_collab(combined)
                            all_records.append(CollabRecord(
                                collab_id=cid,
                                competitor_brand=brand,
                                creator_id=_mk_creator_id("instagram", p.account_handle),
                                platform_code="instagram",
                                post_id=p.post_id,
                                post_url="",
                                post_title="",
                                post_body=p.body_text,
                                hashtags=p.hashtags,
                                published_at=p.published_at,
                                is_paid_collab=is_paid,
                                collab_type="paid" if is_paid else "organic",
                                collab_evidence=evidence,
                                content_theme=_detect_content_theme(combined, p.hashtags),
                                content_format=_detect_content_format(combined),
                                product_mentioned=_extract_products_mentioned(combined),
                                like_count=p.like_count,
                                comment_count=p.comment_count,
                                discovery_method="keyword_search",
                                search_keyword=kw,
                            ))

                    paid_count = sum(1 for r in all_records
                                     if r.search_keyword == kw and r.is_paid_collab)
                    new_count = sum(1 for r in all_records if r.search_keyword == kw)
                    print(f"       → {new_count}条, 付费合作 {paid_count}")

                except Exception as exc:
                    print(f"       ✗ {exc}", file=sys.stderr)

                time.sleep(0.5)

    return all_records


def write_to_db(records: list) -> dict:
    """写入 dim_competitor_kol_collabs"""
    if not records:
        return {"inserted_collabs": 0}
    try:
        import duckdb
    except ImportError:
        return {"inserted_collabs": 0}

    con = duckdb.connect(str(DB_PATH))
    inserted_c = 0

    for r in records:
        d = r.to_dict()
        try:
            con.execute("""
                INSERT OR IGNORE INTO dim_competitor_kol_collabs
                (collab_id, competitor_brand, creator_id, platform_code,
                 post_id, post_url, post_title, post_body, hashtags, published_at, fetched_at,
                 is_paid_collab, collab_type, collab_evidence,
                 content_theme, content_format, product_mentioned,
                 view_count, like_count, comment_count, share_count,
                 is_viral, discovery_method, search_keyword)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [
                d["collab_id"], d["competitor_brand"], d["creator_id"], d["platform_code"],
                d["post_id"], d["post_url"], d["post_title"], d["post_body"],
                d["hashtags"], d["published_at"], d["fetched_at"],
                d["is_paid_collab"], d["collab_type"], d["collab_evidence"],
                d["content_theme"], d["content_format"], d["product_mentioned"],
                d["view_count"], d["like_count"], d["comment_count"], d["share_count"],
                d["is_viral"], d["discovery_method"], d["search_keyword"],
            ])
            inserted_c += 1
        except Exception:
            pass

    # 反向补充 dim_creator_profiles（从 collab 记录里提取创作者）
    inserted_kol = 0
    for r in records:
        try:
            con.execute("""
                INSERT OR IGNORE INTO dim_creator_profiles
                (creator_id, platform_code, account_handle,
                 competitor_collabs, is_paid_collab_flag,
                 data_source, first_seen_at, is_active)
                VALUES (?,?,?,?,?,?,now(),true)
            """, [
                r.creator_id, r.platform_code,
                r.creator_id.split("_", 1)[-1],  # handle from creator_id
                [r.competitor_brand],
                r.is_paid_collab,
                "keyword_search",
            ])
            inserted_kol += 1
        except Exception:
            pass

    con.close()
    return {"inserted_collabs": inserted_c, "inserted_kol_profiles": inserted_kol}


def save_json(records: list, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = output_dir / f"kol_collabs_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": ts,
            "total": len(records),
            "paid_collabs": sum(1 for r in records if r.is_paid_collab),
            "records": [r.to_dict() for r in records],
        }, f, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Keyword Search Collector — KOL Discovery")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--type", default="brand",
                        help="brand/category/product/all")
    parser.add_argument("--platform", default="tiktok",
                        help="tiktok/instagram/youtube/all")
    parser.add_argument("--keyword", default="", help="单个关键词测试")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("=== 关键词配置 ===")
        for kw_type, kws in SEARCH_KEYWORDS.items():
            print(f"\n[{kw_type}] {len(kws)} 个关键词:")
            for k in kws:
                print(f"  '{k['kw']}' → brand={k.get('brand','(任意品牌)')}")
        print(f"\n=== 付费合作识别词 ===")
        print(f"  {PAID_COLLAB_SIGNALS}")
        sys.exit(0)

    if not os.environ.get("TIKHUB_API_KEY"):
        print("⚠ TIKHUB_API_KEY 未设置")
        sys.exit(0)

    kw_types = (["brand", "category", "product"] if args.type == "all"
                else [args.type])
    platforms = (["tiktok", "instagram", "youtube"] if args.platform == "all"
                 else [args.platform])

    if args.keyword:
        print(f"单关键词测试: '{args.keyword}' on {platforms}")
        kw_types = ["brand"]
        SEARCH_KEYWORDS["brand"] = [{"kw": args.keyword, "brand": None, "type": "brand"}]

    print(f"开始搜索: {kw_types} × {platforms}")
    records = run_keyword_search(kw_types, platforms, args.limit)

    paid = sum(1 for r in records if r.is_paid_collab)
    print(f"\n总计: {len(records)} 条, 付费合作: {paid} 条")

    if records:
        out = save_json(records, OUTPUT_DIR)
        print(f"JSON → {out}")
        if args.write_db:
            result = write_to_db(records)
            print(f"DuckDB → collab: {result['inserted_collabs']} 条, "
                  f"KOL档案: {result['inserted_kol_profiles']} 条")
