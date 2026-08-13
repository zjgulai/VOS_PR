"""
监管源监测器 — CPSC / FDA / FTC / Health Canada / EU Safety Gate

是什么：定时拉取各监管机构 RSS/Atom 源，解析成标准 CommentRow 用于 PR Intelligence 风险预警
输入：无（从内置配置读取 RSS URL）
输出：list[RegulatorySignal]，写入 data/processed/regulatory/ 目录
不是什么：不做 NLP 分析，不做风险评分（评分在 Intelligence 层做）

快速启动：
    python -m tools.regulatory.monitor --dry-run
    python -m tools.regulatory.monitor --sources cpsc,fda
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# feedparser 用户安装路径
sys.path.insert(0, str(Path.home() / "Library/Python/3.9/lib/python/site-packages"))

try:
    import feedparser
    _FEEDPARSER_OK = True
except ImportError:
    _FEEDPARSER_OK = False

# ── 监管源注册表 ────────────────────────────────────────────────────
REGULATORY_SOURCES: list[dict] = [
    # ── 美国 ──
    {
        "source_id": "cpsc_recalls",
        "name": "CPSC Recalls",
        "country": "US",
        "category": "product_safety",
        "risk_tier": "P0",
        "url": "https://www.cpsc.gov/cgi-bin/prod.pl?fmt=rss",
        "alt_url": "https://www.cpsc.gov/Recalls",  # 备用（RSS 失败时监测页面变更）
        "keywords_boost": ["baby", "infant", "breast pump", "bottle", "sterilizer",
                           "monitor", "carrier", "nursing", "momcozy", "medela",
                           "willow", "elvie", "recall", "hazard", "fire", "choking"],
    },
    {
        "source_id": "cpsc_saferproducts",
        "name": "CPSC SaferProducts Incidents",
        "country": "US",
        "category": "product_safety",
        "risk_tier": "P0",
        "url": "https://www.saferproducts.gov/rss",
        "alt_url": "https://www.saferproducts.gov/PublicSearch",
        "keywords_boost": ["breast pump", "baby monitor", "bottle sterilizer", "momcozy"],
    },
    {
        "source_id": "fda_warnings",
        "name": "FDA Warning Letters",
        "country": "US",
        "category": "regulatory",
        "risk_tier": "P0",
        "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/warning-letters/rss.xml",
        "keywords_boost": ["breast pump", "baby", "infant", "medical device", "510k"],
    },
    {
        "source_id": "fda_recalls",
        "name": "FDA Medical Device Recalls",
        "country": "US",
        "category": "regulatory",
        "risk_tier": "P0",
        "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-device-recalls/rss.xml",
        "keywords_boost": ["breast pump", "baby monitor", "infant"],
    },
    {
        "source_id": "ftc_actions",
        "name": "FTC Press Releases",
        "country": "US",
        "category": "consumer_protection",
        "risk_tier": "P0",
        "url": "https://www.ftc.gov/feeds/press-releases.xml",
        "keywords_boost": ["fake review", "endorsement", "influencer", "baby", "health claim",
                           "false advertising", "substantiation"],
    },
    # ── 加拿大 ──
    {
        "source_id": "health_canada_recalls",
        "name": "Health Canada Recalls",
        "country": "CA",
        "category": "product_safety",
        "risk_tier": "P0",
        "url": "https://recalls-rappels.canada.ca/en/rss",
        "keywords_boost": ["breast pump", "baby", "infant", "medical device",
                           "momcozy", "wearable", "shenzhen"],
    },
    # ── 英国 ──
    {
        "source_id": "uk_asa",
        "name": "UK ASA Rulings",
        "country": "GB",
        "category": "advertising",
        "risk_tier": "P1",
        "url": "https://www.asa.org.uk/news/rulings.rss",
        "keywords_boost": ["baby", "breast pump", "infant", "health claim", "influencer"],
    },
    {
        "source_id": "uk_opss",
        "name": "UK OPSS Product Safety",
        "country": "GB",
        "category": "product_safety",
        "risk_tier": "P1",
        "url": "https://www.gov.uk/government/organisations/office-for-product-safety-and-standards.atom",
        "keywords_boost": ["baby", "infant", "recall", "breast pump"],
    },
    # ── 欧盟 ──
    {
        "source_id": "eu_safety_gate",
        "name": "EU Safety Gate Alerts",
        "country": "EU",
        "category": "product_safety",
        "risk_tier": "P1",
        "url": "https://ec.europa.eu/safety-gate-alerts/screen/webReport/rss",
        "keywords_boost": ["baby", "infant", "breast pump", "carrier", "monitor"],
    },
    # ── 澳大利亚 ──
    {
        "source_id": "accc_recalls",
        "name": "ACCC Product Recalls AU",
        "country": "AU",
        "category": "product_safety",
        "risk_tier": "P1",
        "url": "https://www.productsafety.gov.au/rss",
        "keywords_boost": ["baby", "infant", "breast pump", "monitor"],
    },
    # ── 法律风险（P0，KleanPal 诉讼已建档）──────────────────────
    {
        "source_id": "classaction_org",
        "name": "ClassAction.org",
        "country": "US",
        "category": "legal_risk",
        "risk_tier": "P0",
        "url": "https://www.classaction.org/news/feed.xml",
        "keywords_boost": [
            "momcozy", "breast pump", "wearable pump", "baby", "infant",
            "sterilizer", "bottle", "monitor", "medela", "willow", "elvie",
            "microplastic", "toxic", "recall", "defect", "injury", "burn",
            "electric", "leak", "class action",
        ],
    },
    {
        "source_id": "tina_org",
        "name": "TINA.org (Truth in Advertising)",
        "country": "US",
        "category": "legal_risk",
        "risk_tier": "P0",
        "url": "https://truthinadvertising.org/feed/",
        "keywords_boost": [
            "momcozy", "breast pump", "baby", "infant", "fake review",
            "false advertising", "influencer", "endorsement", "ftc",
            "deceptive", "misleading", "hidden", "undisclosed",
        ],
    },
    {
        "source_id": "cpsc_enforcement",
        "name": "CPSC Enforcement Actions",
        "country": "US",
        "category": "legal_risk",
        "risk_tier": "P0",
        "url": "https://www.cpsc.gov/cgi-bin/enforcement.pl?fmt=rss",
        "keywords_boost": [
            "baby", "infant", "breast pump", "monitor", "carrier",
            "sterilizer", "momcozy", "penalty", "fine", "civil",
        ],
    },
]


# ── 数据模型 ────────────────────────────────────────────────────────
@dataclass
class RegulatorySignal:
    signal_id: str
    source_id: str
    source_name: str
    country: str
    category: str
    risk_tier: str          # P0 / P1 / P2
    title: str
    url: str
    published_at: str       # ISO 8601
    summary: str
    keywords_matched: list[str] = field(default_factory=list)
    brand_mentions: list[str] = field(default_factory=list)
    fetched_at: str = ""
    raw_tags: list[str] = field(default_factory=list)

    BRAND_WATCHLIST: list[str] = field(
        default_factory=lambda: [
            "momcozy", "medela", "willow", "elvie", "spectra",
            "lansinoh", "baby buddha", "nanit", "owlet", "hatch",
        ],
        repr=False,
    )

    def __post_init__(self) -> None:
        self.fetched_at = datetime.now(timezone.utc).isoformat()
        combined = f"{self.title} {self.summary}".lower()
        self.brand_mentions = [b for b in self.BRAND_WATCHLIST if b in combined]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("BRAND_WATCHLIST", None)
        return d


# ── 采集逻辑 ────────────────────────────────────────────────────────
def _parse_published(entry: Any) -> str:
    for attr in ("published", "updated", "created"):
        raw = getattr(entry, attr, None)
        if raw:
            return str(raw)
    return datetime.now(timezone.utc).isoformat()


def _score_relevance(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]


def fetch_source(source: dict, min_relevance: int = 0) -> list[RegulatorySignal]:
    """拉取单个监管源，返回 RegulatorySignal 列表。min_relevance=0 表示返回所有条目。"""
    if not _FEEDPARSER_OK:
        print(f"[WARN] feedparser not available, skipping {source['source_id']}", file=sys.stderr)
        return []

    signals: list[RegulatorySignal] = []
    try:
        feed = feedparser.parse(source["url"])
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {source['source_id']}: {exc}", file=sys.stderr)
        return []

    for entry in feed.entries:
        title = getattr(entry, "title", "") or ""
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        link = getattr(entry, "link", "") or source["url"]
        published = _parse_published(entry)
        tags = [t.get("term", "") for t in getattr(entry, "tags", [])]

        combined = f"{title} {summary}"
        matched = _score_relevance(combined, source.get("keywords_boost", []))

        if len(matched) < min_relevance:
            continue

        import hashlib
        signal_id = hashlib.sha1(f"{source['source_id']}|{link}|{title}".encode()).hexdigest()[:16]

        signals.append(RegulatorySignal(
            signal_id=signal_id,
            source_id=source["source_id"],
            source_name=source["name"],
            country=source["country"],
            category=source["category"],
            risk_tier=source["risk_tier"],
            title=title,
            url=link,
            published_at=published,
            summary=summary[:1000],
            keywords_matched=matched,
            raw_tags=tags,
        ))

    return signals


def fetch_all(
    source_ids: list[str] | None = None,
    min_relevance: int = 0,
) -> list[RegulatorySignal]:
    """拉取所有（或指定）监管源"""
    sources = REGULATORY_SOURCES
    if source_ids:
        sources = [s for s in sources if s["source_id"] in source_ids]

    all_signals: list[RegulatorySignal] = []
    for source in sources:
        print(f"[INFO] Fetching {source['source_id']} ({source['url'][:60]}...)")
        signals = fetch_source(source, min_relevance=min_relevance)
        print(f"[INFO]   → {len(signals)} signals")
        all_signals.extend(signals)

    return all_signals


def save_signals(signals: list[RegulatorySignal], output_dir: Path) -> Path:
    """保存到 data/processed/regulatory/YYYYMMDD_HHMMSS.json"""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"regulatory_{ts}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "signal_count": len(signals),
                "signals": [s.to_dict() for s in signals],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    return out_path


# ── CLI 入口 ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    PROJ = Path(__file__).resolve().parents[3]
    OUTPUT_DIR = PROJ / "data" / "processed" / "regulatory"

    parser = argparse.ArgumentParser(description="VOC Regulatory Source Monitor")
    parser.add_argument("--sources", default="", help="逗号分隔的 source_id，默认全部")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    parser.add_argument("--min-relevance", type=int, default=0,
                        help="最少关键词命中数才纳入（0=全部）")
    parser.add_argument("--brand-filter", action="store_true",
                        help="只返回有品牌提及的信号")
    args = parser.parse_args()

    source_ids = [s.strip() for s in args.sources.split(",") if s.strip()] or None
    signals = fetch_all(source_ids=source_ids, min_relevance=args.min_relevance)

    if args.brand_filter:
        signals = [s for s in signals if s.brand_mentions]

    p0_signals = [s for s in signals if s.risk_tier == "P0"]
    print(f"\n{'='*60}")
    print(f"Total signals : {len(signals)}")
    print(f"P0 signals    : {len(p0_signals)}")
    print(f"With brand    : {sum(1 for s in signals if s.brand_mentions)}")

    if p0_signals:
        print("\n── P0 Signals ──")
        for s in p0_signals[:10]:
            brands = f" [{','.join(s.brand_mentions)}]" if s.brand_mentions else ""
            print(f"  [{s.source_id}] {s.title[:80]}{brands}")

    if not args.dry_run and signals:
        out = save_signals(signals, OUTPUT_DIR)
        print(f"\nSaved → {out}")
    elif args.dry_run:
        print("\n[dry-run] Not writing output.")
