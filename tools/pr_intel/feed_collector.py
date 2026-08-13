"""
tools/pr_intel/feed_collector.py — 媒体 RSS 采集器

是什么：采集 PR Intelligence 所需的核心媒体 RSS 源，写入 DuckDB pr_articles 表
输入：MEDIA_RSS_SOURCES 配置表（30 个核心源）
输出：data/processed/pr_intel/YYYYMMDD_HHMMSS.json + DuckDB pr_articles 写入
不是什么：不做 LLM 分析（LLM 层由下游处理），不做去重（DuckDB PRIMARY KEY 自动处理）

快速启动：
    python3 tools/pr_intel/feed_collector.py --dry-run
    python3 tools/pr_intel/feed_collector.py --sources pr_wire,tech
    python3 tools/pr_intel/feed_collector.py --write-db

依赖：feedparser（已安装），duckdb（已安装）
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 用户安装路径
sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))

try:
    import feedparser
    _FEEDPARSER_OK = True
except ImportError:
    _FEEDPARSER_OK = False

PROJ = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJ / "data" / "processed" / "pr_intel"
DB_PATH = PROJ / "data" / "warehouse" / "voc.duckdb"


# ── 媒体 RSS 源注册表 ────────────────────────────────────────
# 分类：pr_wire（新闻稿分发）/ tech（科技商业媒体）/ baby_media（母婴垂类媒体）
#       regulatory（已在 monitor.py 覆盖，此处不重复）/ legal（法律风险）
MEDIA_RSS_SOURCES: list[dict] = [

    # ── PR Wire：竞品新品/融资/重大事件首发 ──────────────────
    {
        "source_id": "globenewswire_baby",
        "name": "GlobeNewswire – Baby & Maternity",
        "category": "pr_wire",
        "country": "US",
        "language": "en",
        "base_weight": 70,
        "url": "https://www.globenewswire.com/RssFeed/industry/Baby+and+Maternity",
        "keywords_boost": ["momcozy", "breast pump", "wearable pump", "medela", "willow",
                           "elvie", "eufy", "spectra", "lansinoh", "baby monitor", "sterilizer",
                           "melody inbra", "freestyle mini", "willow sync", "willow wave",
                           "motif aura glow", "spectra premier", "discreetduo flow",
                           "eufy S1", "eufy S1 Pro"],
    },
    {
        "source_id": "prnewswire_baby",
        "name": "PR Newswire – Baby Products",
        "category": "pr_wire",
        "country": "US",
        "language": "en",
        "base_weight": 72,
        "url": "https://www.prnewswire.com/rss/news-releases-list.rss?category=CPG",
        "keywords_boost": ["breast pump", "wearable", "momcozy", "medela", "willow",
                           "breast feeding", "baby", "infant", "maternal"],
    },
    {
        "source_id": "businesswire_health",
        "name": "BusinessWire – Health & Wellness",
        "category": "pr_wire",
        "country": "US",
        "language": "en",
        "base_weight": 70,
        "url": "https://feed.businesswire.com/rss/home/?rss=G22&lang=en",
        "keywords_boost": ["breast pump", "momcozy", "willow", "elvie", "femtech",
                           "maternal", "recall", "lawsuit"],
    },

    # ── Tech / FemTech / Business 媒体：竞品战略情报 ──────────
    {
        "source_id": "techcrunch",
        "name": "TechCrunch",
        "category": "tech",
        "country": "US",
        "language": "en",
        "base_weight": 72,
        "url": "https://techcrunch.com/feed/",
        "keywords_boost": ["breast pump", "femtech", "willow", "elvie", "chiaro",
                           "nanit", "owlet", "baby tech", "maternal health"],
    },
    {
        "source_id": "sifted",
        "name": "Sifted – European Tech",
        "category": "tech",
        "country": "GB",
        "language": "en",
        "base_weight": 68,
        "url": "https://sifted.eu/feed",
        "keywords_boost": ["elvie", "chiaro", "femtech", "willow", "breast pump",
                           "maternal", "women's health"],
    },
    {
        "source_id": "modernretail",
        "name": "Modern Retail",
        "category": "tech",
        "country": "US",
        "language": "en",
        "base_weight": 70,
        "url": "https://www.modernretail.co/feed/",
        "keywords_boost": ["momcozy", "breast pump", "baby", "target", "walmart",
                           "DTC", "dupe", "willow", "elvie", "medela"],
    },
    {
        "source_id": "retaildive",
        "name": "Retail Dive",
        "category": "tech",
        "country": "US",
        "language": "en",
        "base_weight": 65,
        "url": "https://www.retaildive.com/feeds/news/",
        "keywords_boost": ["baby", "target baby", "walmart baby", "infant",
                           "momcozy", "breast pump"],
    },
    {
        "source_id": "fortune",
        "name": "Fortune – Health",
        "category": "tech",
        "country": "US",
        "language": "en",
        "base_weight": 72,
        "url": "https://fortune.com/feed/",
        "keywords_boost": ["breast pump", "femtech", "maternal", "momcozy",
                           "women's health", "baby"],
    },

    # ── 母婴垂类媒体：编辑选题/竞品评测追踪 ──────────────────
    {
        "source_id": "babylist_blog",
        "name": "Babylist Blog",
        "category": "baby_media",
        "country": "US",
        "language": "en",
        "base_weight": 82,
        "url": "https://www.babylist.com/hello-baby/feed",
        "keywords_boost": ["breast pump", "wearable pump", "momcozy", "medela",
                           "willow", "best", "review", "monitor"],
    },
    {
        "source_id": "thebump",
        "name": "The Bump",
        "category": "baby_media",
        "country": "US",
        "language": "en",
        "base_weight": 80,
        "url": "https://www.thebump.com/rss/news",
        "keywords_boost": ["breast pump", "wearable", "hands-free pump",
                           "momcozy", "medela", "best pump"],
    },
    {
        "source_id": "parents_mag",
        "name": "Parents Magazine",
        "category": "baby_media",
        "country": "US",
        "language": "en",
        "base_weight": 78,
        "url": "https://www.parents.com/feeds/all.rss",
        "keywords_boost": ["breast pump", "momcozy", "wearable pump", "best baby",
                           "review", "award"],
    },
    {
        "source_id": "babycenter_news",
        "name": "BabyCenter",
        "category": "baby_media",
        "country": "US",
        "language": "en",
        "base_weight": 72,
        "url": "https://www.babycenter.com/rss/news.xml",
        "keywords_boost": ["breast pump", "momcozy", "wearable", "formula",
                           "safety", "recall"],
    },
    {
        "source_id": "whattoexpect",
        "name": "What to Expect",
        "category": "baby_media",
        "country": "US",
        "language": "en",
        "base_weight": 72,
        "url": "https://www.whattoexpect.com/news/rss.xml",
        "keywords_boost": ["breast pump", "wearable pump", "momcozy", "medela",
                           "baby gear", "best"],
    },
    {
        "source_id": "motherly",
        "name": "Motherly",
        "category": "baby_media",
        "country": "US",
        "language": "en",
        "base_weight": 65,
        "url": "https://www.mother.ly/feed/",
        "keywords_boost": ["breast pump", "momcozy", "wearable", "maternal health",
                           "postpartum", "working mom"],
    },
    {
        "source_id": "motherandbaby_uk",
        "name": "Mother & Baby UK",
        "category": "baby_media",
        "country": "GB",
        "language": "en",
        "base_weight": 78,
        "url": "https://www.motherandbaby.com/feed",
        "keywords_boost": ["breast pump", "momcozy", "medela", "award",
                           "best baby", "wearable"],
    },
    {
        "source_id": "netmums",
        "name": "Netmums",
        "category": "baby_media",
        "country": "GB",
        "language": "en",
        "base_weight": 72,
        "url": "https://www.netmums.com/feed/rss",
        "keywords_boost": ["breast pump", "momcozy", "medela", "review",
                           "best baby", "pumping"],
    },

    # ── 女性/文化媒体：议题设定/反叙事监控 ───────────────────
    {
        "source_id": "marieclaire",
        "name": "Marie Claire",
        "category": "women_media",
        "country": "US",
        "language": "en",
        "base_weight": 68,
        "url": "https://www.marieclaire.com/rss/all.xml/",
        "keywords_boost": ["breast pump", "breastfeeding", "pumping", "maternal",
                           "working mom", "femtech", "momcozy"],
    },
    {
        "source_id": "womenshealth",
        "name": "Women's Health",
        "category": "women_media",
        "country": "US",
        "language": "en",
        "base_weight": 67,
        "url": "https://www.womenshealthmag.com/rss/all.xml/",
        "keywords_boost": ["breast pump", "breastfeeding", "momcozy",
                           "postpartum", "maternal health"],
    },
    {
        "source_id": "fastcompany",
        "name": "Fast Company",
        "category": "women_media",
        "country": "US",
        "language": "en",
        "base_weight": 70,
        "url": "https://www.fastcompany.com/rss.xml",
        "keywords_boost": ["femtech", "maternal", "breast pump", "willow",
                           "elvie", "momcozy", "working parents"],
    },

    # ── 独立测评媒体：榜单变化/竞品评测 ──────────────────────
    {
        "source_id": "wirecutter",
        "name": "Wirecutter (NYT)",
        "category": "review_media",
        "country": "US",
        "language": "en",
        "base_weight": 90,
        "url": "https://www.nytimes.com/wirecutter/feed/",
        "keywords_boost": ["breast pump", "baby monitor", "wearable pump",
                           "momcozy", "medela", "willow", "best"],
    },
    {
        "source_id": "goodhousekeeping",
        "name": "Good Housekeeping",
        "category": "review_media",
        "country": "US",
        "language": "en",
        "base_weight": 76,
        "url": "https://www.goodhousekeeping.com/rss/all.xml",
        "keywords_boost": ["breast pump", "wearable pump", "momcozy", "medela",
                           "best baby", "review"],
    },
    {
        "source_id": "reviewed_usatoday",
        "name": "Reviewed (USA TODAY)",
        "category": "review_media",
        "country": "US",
        "language": "en",
        "base_weight": 75,
        "url": "https://reviewed.usatoday.com/rss",
        "keywords_boost": ["breast pump", "wearable pump", "momcozy",
                           "best baby", "review"],
    },

    # ── 法律风险监测 ──────────────────────────────────────────
    {
        "source_id": "classaction_org",
        "name": "ClassAction.org",
        "category": "legal",
        "country": "US",
        "language": "en",
        "base_weight": 92,
        "url": "https://www.classaction.org/news/feed.xml",
        "keywords_boost": ["momcozy", "breast pump", "baby", "infant", "sterilizer",
                           "monitor", "wearable", "medela", "willow", "nanit", "owlet",
                           "microplastic", "plastic", "recall", "defect", "injury"],
    },
    {
        "source_id": "tina_org",
        "name": "TINA.org (Truth in Advertising)",
        "category": "legal",
        "country": "US",
        "language": "en",
        "base_weight": 85,
        "url": "https://truthinadvertising.org/feed/",
        "keywords_boost": ["momcozy", "breast pump", "baby", "infant", "fake review",
                           "false advertising", "influencer", "endorsement"],
    },

    # ── 母婴英语垂类（英国/澳大利亚）─────────────────────────
    {
        "source_id": "madeformums",
        "name": "Made for Mums",
        "category": "baby_media",
        "country": "GB",
        "language": "en",
        "base_weight": 68,
        "url": "https://www.madeformums.com/feed/",
        "keywords_boost": ["breast pump", "wearable pump", "momcozy", "medela",
                           "award", "best", "review"],
    },

    # ── 行业/供应链媒体 ──────────────────────────────────────
    {
        "source_id": "businessinsider_retail",
        "name": "Business Insider – Retail",
        "category": "tech",
        "country": "US",
        "language": "en",
        "base_weight": 62,
        "url": "https://markets.businessinsider.com/rss/news",
        "keywords_boost": ["momcozy", "breast pump", "willow", "medela",
                           "baby", "femtech"],
    },
]


# ── 数据模型 ─────────────────────────────────────────────────
@dataclass
class PRArticle:
    article_id: str
    source_id: str
    source_name: str
    source_type: str
    country: str
    language: str
    title: str
    url: str
    published_at: str
    fetched_at: str
    body_snippet: str
    keywords_matched: list
    brand_mentions: list
    risk_tier: str

    BRAND_WATCHLIST: list = field(
        default_factory=lambda: [
            # 吸奶器竞品 v1.0（2026-08-12业务确认）
            "momcozy", "eufy", "elvie", "willow", "spectra", "medela",
            "frida", "motif medical", "lansinoh", "babybuddha", "ameda", "zomee",
            "lola lykke", "freemie", "haakaa", "ardo", "nuk",
            # 喂养电器竞品 v1.0
            "baby brezza", "grownsy", "wabi baby", "papablic",
            "tommee tippee", "dr brown", "chicco", "munchkin", "beaba",
            # KleanPal 专项风险监测
            "kleanpal", "klean pal",
        ],
        repr=False,
    )
    RISK_KEYWORDS: list = field(
        default_factory=lambda: [
            "recall", "lawsuit", "class action", "injury", "defect",
            "unsafe", "warning", "investigation", "complaint", "ban",
            "microplastic", "toxic", "hazard", "cancer", "fire",
            "senate", "ftc", "fda", "cpsc", "health canada",
            # KleanPal/喂养电器专项风险词
            "sterilizer crack", "sterilizer peeling", "coating peeling",
            "plastic fragment", "sterilizer recall",
        ],
        repr=False,
    )

    def __post_init__(self) -> None:
        combined = f"{self.title} {self.body_snippet}".lower()
        self.brand_mentions = [b for b in self.BRAND_WATCHLIST if b in combined]
        risk_hits = [r for r in self.RISK_KEYWORDS if r in combined]
        self.risk_tier = "P0" if risk_hits else ("P1" if self.brand_mentions else "none")

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("BRAND_WATCHLIST", None)
        d.pop("RISK_KEYWORDS", None)
        return d


# ── 采集逻辑 ─────────────────────────────────────────────────
def _mk_article_id(source_id: str, url: str, title: str) -> str:
    raw = f"{source_id}|{url}|{title}".encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()[:20]


def _parse_date(entry: object) -> str:
    for attr in ("published", "updated", "created"):
        val = getattr(entry, attr, None)
        if val:
            return str(val)
    return datetime.now(timezone.utc).isoformat()


def fetch_source(source: dict, min_keyword_hits: int = 0) -> list[PRArticle]:
    if not _FEEDPARSER_OK:
        print(f"[WARN] feedparser not available", file=sys.stderr)
        return []

    try:
        feed = feedparser.parse(source["url"])
    except Exception as exc:
        print(f"[ERROR] {source['source_id']}: {exc}", file=sys.stderr)
        return []

    articles = []
    boost_kws = [k.lower() for k in source.get("keywords_boost", [])]
    now = datetime.now(timezone.utc).isoformat()

    for entry in feed.entries:
        title = getattr(entry, "title", "") or ""
        url = getattr(entry, "link", "") or source["url"]
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        published = _parse_date(entry)

        combined = f"{title} {summary}".lower()
        matched = [k for k in boost_kws if k in combined]

        if len(matched) < min_keyword_hits:
            continue

        article_id = _mk_article_id(source["source_id"], url, title)
        articles.append(PRArticle(
            article_id=article_id,
            source_id=source["source_id"],
            source_name=source["name"],
            source_type=source["category"],
            country=source.get("country", "US"),
            language=source.get("language", "en"),
            title=title,
            url=url,
            published_at=published,
            fetched_at=now,
            body_snippet=summary[:1000],
            keywords_matched=matched,
            brand_mentions=[],   # __post_init__ 填充
            risk_tier="none",    # __post_init__ 填充
        ))

    return articles


def fetch_all(
    category_filter: Optional[list] = None,
    min_keyword_hits: int = 0,
) -> list[PRArticle]:
    sources = MEDIA_RSS_SOURCES
    if category_filter:
        sources = [s for s in sources if s["category"] in category_filter]

    all_articles = []
    for source in sources:
        print(f"[INFO] {source['source_id']:35} ({source['url'][:55]}...)")
        try:
            arts = fetch_source(source, min_keyword_hits=min_keyword_hits)
            brand_count = sum(1 for a in arts if a.brand_mentions)
            p0_count = sum(1 for a in arts if a.risk_tier == "P0")
            print(f"         → {len(arts)} 条, 含品牌 {brand_count}, P0风险 {p0_count}")
            all_articles.extend(arts)
        except Exception as exc:
            print(f"[ERROR] {source['source_id']}: {exc}")

    return all_articles


def write_to_db(articles: list[PRArticle]) -> int:
    """写入 DuckDB pr_articles 表，主键冲突自动跳过"""
    if not articles:
        return 0

    try:
        import duckdb
    except ImportError:
        print("[ERROR] duckdb not available")
        return 0

    con = duckdb.connect(str(DB_PATH))
    inserted = 0
    for a in articles:
        d = a.to_dict()
        try:
            con.execute("""
                INSERT OR IGNORE INTO pr_articles
                (article_id, source_id, source_name, source_type, country, language,
                 title, url, published_at, fetched_at, body_snippet,
                 keywords_matched, brand_mentions, risk_tier)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, [
                d["article_id"], d["source_id"], d["source_name"], d["source_type"],
                d["country"], d["language"], d["title"], d["url"],
                d["published_at"], d["fetched_at"], d["body_snippet"],
                d["keywords_matched"], d["brand_mentions"], d["risk_tier"],
            ])
            inserted += 1
        except Exception:
            pass
    con.close()
    return inserted


def save_json(articles: list[PRArticle], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = output_dir / f"pr_intel_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "article_count": len(articles),
                "p0_count": sum(1 for a in articles if a.risk_tier == "P0"),
                "brand_mention_count": sum(1 for a in articles if a.brand_mentions),
                "articles": [a.to_dict() for a in articles],
            },
            f, ensure_ascii=False, indent=2,
        )
    return out


# ── CLI ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PR Intelligence Media RSS Collector")
    parser.add_argument("--sources", default="",
                        help="逗号分隔的 category 过滤，如 pr_wire,legal,tech")
    parser.add_argument("--dry-run", action="store_true",
                        help="只统计，不写文件和数据库")
    parser.add_argument("--write-db", action="store_true",
                        help="写入 DuckDB（默认只写 JSON）")
    parser.add_argument("--min-keywords", type=int, default=0,
                        help="最少关键词命中数才入库（默认0=全部）")
    parser.add_argument("--brand-only", action="store_true",
                        help="只返回有品牌提及的条目")
    args = parser.parse_args()

    cats = [s.strip() for s in args.sources.split(",") if s.strip()] or None
    articles = fetch_all(category_filter=cats, min_keyword_hits=args.min_keywords)

    if args.brand_only:
        articles = [a for a in articles if a.brand_mentions]

    p0 = [a for a in articles if a.risk_tier == "P0"]
    p1 = [a for a in articles if a.risk_tier == "P1"]

    print(f"\n{'='*60}")
    print(f"总条目   : {len(articles)}")
    print(f"P0 风险  : {len(p0)}")
    print(f"P1 含品牌: {len(p1)}")

    if p0:
        print("\n── P0 信号（前5条）──")
        for a in p0[:5]:
            brands = f" [{','.join(a.brand_mentions)}]" if a.brand_mentions else ""
            kws = f" kw={a.keywords_matched[:2]}"
            print(f"  [{a.source_id}] {a.title[:70]}{brands}{kws}")

    if not args.dry_run:
        out = save_json(articles, OUTPUT_DIR)
        print(f"\nJSON → {out}")

        if args.write_db:
            inserted = write_to_db(articles)
            print(f"DuckDB → 插入 {inserted} 条（重复自动跳过）")
    else:
        print("\n[dry-run] 不写出文件")
