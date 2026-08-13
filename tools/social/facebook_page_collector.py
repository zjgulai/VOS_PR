"""
tools/social/facebook_page_collector.py — Facebook 官方主页采集器（Apify）

是什么：通过 Apify facebook-posts-scraper Actor 采集竞品 Facebook 官方主页帖子
用途：S2 需求——竞品社媒营销动作监控（Facebook 主页帖子）

为什么用 Apify：
  - Meta Graph API 不开放第三方采集 Facebook 公开页面帖子
  - Apify apify/facebook-posts-scraper 是目前最成熟的方案
  - 费用：$0.005-0.008/帖（97,976 用户，4.61星）
  - 接受风险：Q4=A（用户已确认接受第三方工具 ToS 风险）

actual_status: CODE_UNVERIFIED
  → 需要 APIFY_API_KEY 才能运行
  → 在部署服务器配置后验证

业务价值评估（诚实记录）：
  - 竞品主战场在 Instagram(53%) + TikTok，不在 Facebook 主页
  - Baby Brezza 274帖/月但主要在 Instagram
  - Facebook 主页内容通常是 Instagram 的转发
  - 优先级：P2（不阻塞 S2 核心需求）

快速测试：
    python3 tools/social/facebook_page_collector.py --dry-run
    python3 tools/social/facebook_page_collector.py --page babybrezza --limit 10
    python3 tools/social/facebook_page_collector.py --all --limit 20 --write-db
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

from tools.social.dictionary import get_brand_watchlist, get_facebook_pages


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

APIFY_BASE = "https://api.apify.com/v2"
APIFY_ACTOR = "apify~facebook-posts-scraper"

def _competitor_pages() -> list[dict]:
    pages = get_facebook_pages()
    return [{"brand": bk, "page_url": url} for bk, url in pages.items()]


def _get_apify_token() -> str:
    token = os.environ.get("APIFY_API_KEY", "")
    if not token:
        raise EnvironmentError(
            "APIFY_API_KEY not set.\n"
            "  获取：https://console.apify.com → Settings → Integrations → API tokens\n"
            "  设置：export APIFY_API_KEY='your-token'\n"
            "  费用：$0.005-0.008/帖，免费计划可采集 500 帖"
        )
    return token


def _mk_post_id(brand: str, post_id: str) -> str:
    raw = f"facebook|{brand}|{post_id}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:20]


@dataclass
class FacebookPost:
    post_id: str
    platform_code: str = "facebook"
    account_handle: str = ""
    account_type: str = "competitor"
    competitor_brand: str = ""
    content_type: str = "post"
    body_text: str = ""
    hashtags: list = field(default_factory=list)
    published_at: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    view_count: int = 0
    engagement_rate: float = 0.0
    is_viral_flag: bool = False
    is_paid_collab: bool = False
    brand_mentions: list = field(default_factory=list)
    post_url: str = ""
    country_code: str = "US"
    language: str = "en"
    is_processed: bool = False

    def __post_init__(self) -> None:
        combined = self.body_text.lower()
        self.brand_mentions = [b for b in get_brand_watchlist() if b in combined]
        self.hashtags = _re.findall(r"#(\w+)", self.body_text)
        paid_signals = ["#ad", "#sponsored", "#gifted", "#partner", "paid partnership"]
        self.is_paid_collab = any(s in self.body_text.lower() for s in paid_signals)

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_page_posts(page_url: str, brand: str, limit: int = 20,
                     days_back: int = 30) -> list:
    """调用 Apify Actor 采集 Facebook 主页帖子"""
    token = _get_apify_token()

    payload = {
        "startUrls": [{"url": page_url}],
        "resultsLimit": limit,
        "onlyPostsNewerThan": f"{days_back} days",
    }

    resp = httpx.post(
        f"{APIFY_BASE}/acts/{APIFY_ACTOR}/run-sync-get-dataset-items",
        params={"token": token},
        json=payload,
        timeout=120.0,
    )

    if resp.status_code == 401:
        raise EnvironmentError("APIFY_API_KEY 无效（401）")
    if resp.status_code not in (200, 201):
        print(f"  [WARN] {page_url}: HTTP {resp.status_code}", file=sys.stderr)
        return []

    items = resp.json()
    if not isinstance(items, list):
        items = []
    posts = []
    for item in items:
        pid = item.get("id") or item.get("postId") or item.get("url", "")[-20:]
        text = item.get("text") or item.get("message") or ""
        timestamp = item.get("timestamp") or item.get("time") or ""
        likes = item.get("likes") or 0
        comments = item.get("comments") or 0
        shares = item.get("shares") or 0
        def _i(v):
            try:
                return int(v)
            except (TypeError, ValueError):
                return 0
        post_url = item.get("url") or item.get("postUrl") or ""

        if isinstance(timestamp, (int, float)) and timestamp > 0:
            published = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
        elif isinstance(timestamp, str) and timestamp:
            published = timestamp
        else:
            published = ""

        posts.append(FacebookPost(
            post_id=_mk_post_id(brand, str(pid)),
            account_handle=page_url.rstrip("/").split("/")[-1],
            competitor_brand=brand,
            content_type="video" if item.get("isVideo") else "post",
            body_text=text[:500],
            published_at=published,
            like_count=_i(likes),
            comment_count=_i(comments),
            share_count=_i(shares),
            is_viral_flag=_i(likes) > 1000 or _i(shares) > 100,
            post_url=post_url,
        ))

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
                 published_at, fetched_at, like_count, comment_count, share_count,
                 is_viral_flag, is_paid_collab, brand_mentions,
                 country_code, language, is_processed)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [
                d["post_id"], d["platform_code"], d["account_handle"], d["account_type"],
                d["competitor_brand"], d["content_type"], d["body_text"], d["hashtags"],
                d["published_at"], d["fetched_at"], d["like_count"], d["comment_count"],
                d["share_count"], d["is_viral_flag"], d["is_paid_collab"], d["brand_mentions"],
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
    out = output_dir / f"facebook_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": ts, "post_count": len(posts),
                   "posts": [p.to_dict() for p in posts]},
                  f, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Facebook Page Collector via Apify")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--page", default="", help="竞品页面名称，如 babybrezza")
    parser.add_argument("--all", action="store_true", help="采集全部竞品页面")
    parser.add_argument("--priority", default="P0", choices=["P0", "P1"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--days-back", type=int, default=30, help="采集最近N天的帖子")
    parser.add_argument("--write-db", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        pages = _competitor_pages()
        print(f"竞品 Facebook 主页（来自词典）: {len(pages)} 个")
        for p in pages:
            print(f"  {p['brand']:15} → {p['page_url']}")
        print(f"\n⚠ 需要 APIFY_API_KEY（费用约 $0.006/帖）")
        print(f"  设置：export APIFY_API_KEY='your-token'")
        print(f"  获取：https://console.apify.com → Settings → Integrations")
        sys.exit(0)

    if not os.environ.get("APIFY_API_KEY"):
        print("⚠ APIFY_API_KEY 未设置")
        print("  获取：https://console.apify.com → Settings → Integrations")
        sys.exit(0)

    pages_to_run = []
    pages = _competitor_pages()

    if args.page:
        pages_to_run = [p for p in pages
                        if p["brand"] == args.page or p["page_url"].endswith(args.page)]
    else:
        pages_to_run = pages if args.all else pages[:6]

    all_posts = []
    for page_cfg in pages_to_run:
        print(f"  {page_cfg['brand']} ({page_cfg['page_url']})...")
        try:
            posts = fetch_page_posts(
                page_cfg["page_url"], page_cfg["brand"],
                args.limit, args.days_back,
            )
            viral = sum(1 for p in posts if p.is_viral_flag)
            paid = sum(1 for p in posts if p.is_paid_collab)
            print(f"       → {len(posts)} 条, 高互动 {viral}, 付费标注 {paid}")
            all_posts.extend(posts)
        except EnvironmentError as e:
            print(f"  ✗ {e}")
            break
        except Exception as exc:
            print(f"  ✗ {page_cfg['brand']}: {exc}", file=sys.stderr)
        time.sleep(2.0)

    print(f"\n总计: {len(all_posts)} 条")
    if all_posts:
        out = save_json(all_posts, OUTPUT_DIR)
        print(f"JSON → {out}")
        if args.write_db:
            inserted = write_to_db(all_posts)
            print(f"DuckDB → {inserted} 条")
