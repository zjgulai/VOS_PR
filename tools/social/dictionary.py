"""竞品词典统一加载器。

所有采集器从这里读取品牌/handle/关键词，替代各采集器内的 BRAND_WATCHLIST 硬编码。
单一真源：config/competitor_dictionary.json。
"""
from __future__ import annotations

import json
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
DICT_PATH = PROJ / "config" / "competitor_dictionary.json"

_cache: dict | None = None


def load_dictionary() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(DICT_PATH.read_text(encoding="utf-8"))
    return _cache


def get_brand_watchlist() -> list[str]:
    return load_dictionary()["brand_watchlist_flat"]


def get_competitor_accounts(platform: str) -> list[dict]:
    """返回 handle 非空的竞品账号列表 [{brand, name, handle, priority}]。"""
    d = load_dictionary()
    out: list[dict] = []
    for line in d["competitors"]["pump"] + d["competitors"]["feeding_appliance"]:
        handle = (line.get(platform) or "").strip()
        if handle:
            out.append({
                "brand": line["brand_key"],
                "name": line["name"],
                "handle": handle,
                "priority": line["priority"],
            })
    return out


def get_facebook_pages() -> dict[str, str]:
    return load_dictionary().get("facebook_pages", {})


def get_risk_keywords() -> list[dict]:
    return load_dictionary()["risk_keywords"]


def get_kleanpal_keywords() -> list[str]:
    return load_dictionary()["kleanpal_risk_keywords"]
