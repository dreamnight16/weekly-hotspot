"""并行搜索 — 同时搜 DDG + Bing，合并去重。"""
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from chinese_scraper_utils import search_web as _search_ddg

logger = logging.getLogger("weekly.search")

BING_API_KEY = os.environ.get("BING_API_KEY", "")

_BING_LOCK = _search_ddg.__self__ if hasattr(_search_ddg, "__self__") else None


def _search_bing(query: str, max_results: int = 10) -> list[dict]:
    """Bing Web Search API。"""
    import urllib.request
    import urllib.parse
    import json

    if not BING_API_KEY:
        return []

    encoded = urllib.parse.quote(query)
    url = f"https://api.bing.microsoft.com/v7.0/search?q={encoded}&count={max_results}&mkt=zh-CN"
    req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": BING_API_KEY})
    try:
        # Scheme is hardcoded to https; not attacker-controlled.
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("[search] Bing 搜索失败: %s", exc)
        return []

    results = []
    for item in data.get("webPages", {}).get("value", [])[:max_results]:
        results.append({
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", ""),
        })
    return results


def search_event(query: str, max_results: int = 10) -> list[dict]:
    """并行搜索 DDG + Bing，URL 去重，标题相似去重。"""
    ddg_results = []
    bing_results = []

    # DDG 有内置限速（3s interval），先跑 DDG、同时跑 Bing
    with ThreadPoolExecutor(max_workers=2) as pool:
        ddg_future = pool.submit(_search_ddg, query, max_results)
        bing_future = pool.submit(_search_bing, query, max_results) if BING_API_KEY else None

        try:
            ddg_results = [
                {"title": r.title, "url": r.url, "snippet": r.snippet}
                for r in ddg_future.result()
            ]
        except Exception as exc:
            logger.warning("[search] DDG 搜索失败: %s", exc)

        if bing_future:
            try:
                bing_results = bing_future.result()
            except Exception as exc:
                logger.warning("[search] Bing 结果解析失败: %s", exc)

    # Merge: URL exact dedup, then title fuzzy dedup
    seen_urls = set()
    merged = []

    for r in ddg_results:
        url_key = r["url"].rstrip("/").lower()
        if url_key not in seen_urls:
            seen_urls.add(url_key)
            merged.append(r)

    for r in bing_results:
        url_key = r["url"].rstrip("/").lower()
        if url_key in seen_urls:
            continue
        # Title fuzzy dedup
        dup = False
        for existing in merged:
            if _title_similar(r["title"], existing["title"]):
                dup = True
                break
        if not dup:
            seen_urls.add(url_key)
            merged.append(r)

    return merged[:max_results]


def _title_similar(a: str, b: str) -> bool:
    """简单 Jaccard 字符级相似度，>0.7 视为重复标题。"""
    if not a or not b:
        return False
    set_a = set(a.replace(" ", ""))
    set_b = set(b.replace(" ", ""))
    if not set_a or not set_b:
        return False
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union > 0.7
