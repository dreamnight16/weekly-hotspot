"""
Search the web for real news/articles about an event.
Uses ddgs (DuckDuckGo, free, no API key).
"""
from ddgs import DDGS


def search_event(title: str, max_results: int = 10) -> list[dict]:
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(f"{title} 事件 新闻", max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("url", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })
    except Exception as e:
        print(f"    [search] error: {e}")

    return results
