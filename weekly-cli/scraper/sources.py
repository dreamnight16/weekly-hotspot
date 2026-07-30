"""Scrape sources: Weibo, Zhihu, HackerNews.

Provides `scrape_all()` which wraps the three-source scrape, deduplication,
and conversion to pipeline event dicts, then caches the result.
"""
from __future__ import annotations

import logging
from typing import Any

from chinese_scraper_utils import (
    scrape_hackernews_top,
    scrape_weibo_hot,
    scrape_zhihu_hot,
)
from scraper.cache import save_cache

logger = logging.getLogger(__name__)


def scrape_all() -> list[dict]:
    """Scrape all sources, deduplicate, convert to event dicts, and cache.

    Returns a list of event dicts with ``title`` and ``summary`` keys.
    Returns an empty list when every source returns nothing.
    """
    raw_topics: list[Any] = (
        scrape_weibo_hot()
        + scrape_zhihu_hot()
        + scrape_hackernews_top()
    )
    logger.info("  抓取到 %d 个话题（微博+知乎+HN）", len(raw_topics))

    if not raw_topics:
        return []

    # Deduplicate by title
    seen: set[str] = set()
    deduped: list[Any] = []
    for t in raw_topics:
        key = t.title.lower().replace(" ", "")
        if key not in seen:
            seen.add(key)
            deduped.append(t)
    logger.info("  去重后: %d 个话题", len(deduped))

    # Convert to event dicts for the pipeline
    events = [
        {"title": t.title, "summary": f"{t.summary}\n来源: {t.url}"}
        for t in deduped
    ]
    save_cache(events)
    return events
