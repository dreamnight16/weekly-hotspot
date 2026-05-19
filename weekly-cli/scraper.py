"""
Scrape real hot topics from public APIs.
No AI — just HTTP with proper headers.
"""
import httpx

# Weibo needs a cookie set to pass the API gate. Getting it from the homepage first.
WEIBO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://weibo.com/",
    "X-Requested-With": "XMLHttpRequest",
}

ZHIHU_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.zhihu.com/hot",
    "Origin": "https://www.zhihu.com",
}


def _weibo_item_to_topic(item: dict) -> dict | None:
    word = item.get("word") or item.get("note") or item.get("title")
    if not word or word in ("实时热搜", "微博热搜", "热搜榜"):
        return None
    raw_url = item.get("scheme", "") or item.get("url", "") or ""
    url = raw_url if raw_url.startswith("http") else f"https://s.weibo.com/weibo?q={word}"
    return {
        "title": word.strip().lstrip("#").rstrip("#"),
        "summary": f"热搜第{item.get('rank', '?')}名 · 热度 {item.get('raw_hot', item.get('hot', '?'))}",
        "url": url,
        "source": "微博热搜",
        "raw_score": item.get("raw_hot", item.get("hot", 0)) or 0,
    }


def scrape_weibo(client: httpx.Client) -> list[dict]:
    """Scrape Weibo hot search. Needs cookie jar from homepage."""
    try:
        # First visit homepage to get cookies
        client.get("https://weibo.com/", timeout=15)

        # Then hit the hot search API
        resp = client.get(
            "https://weibo.com/ajax/side/hotSearch",
            headers=WEIBO_HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"  [weibo] HTTP {resp.status_code}")
            return []
        data = resp.json()
        items = (
            data.get("data", {}).get("realtime", [])
            or data.get("data", {}).get("hotgovs", [])
            or []
        )
        results = []
        for item in items:
            topic = _weibo_item_to_topic(item)
            if topic:
                results.append(topic)
        print(f"  [weibo] scraped {len(results)} topics")
        return results
    except Exception as e:
        print(f"  [weibo] error: {e}")
        return []


def scrape_zhihu(client: httpx.Client) -> list[dict]:
    """Scrape Zhihu hot list. Desktop API endpoint."""
    try:
        resp = client.get(
            "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true",
            headers=ZHIHU_HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"  [zhihu] HTTP {resp.status_code}")
            return []
        data = resp.json()
        items = data.get("data", [])
        results = []
        for i, item in enumerate(items):
            target = item.get("target", {})
            title = target.get("title", "").strip()
            if not title:
                continue
            url = target.get("url", "")
            if not url:
                qid = target.get("id", "")
                url = f"https://www.zhihu.com/question/{qid}" if qid else ""
            if url and not url.startswith("http"):
                url = f"https://www.zhihu.com{url}"
            results.append({
                "title": title,
                "summary": f"知乎热榜第{i + 1}名 · {target.get('excerpt', '')[:80] or '热度话题'}",
                "url": url,
                "source": "知乎热榜",
                "raw_score": target.get("heat", 0) or target.get("follower_count", 0) or 0,
            })
        print(f"  [zhihu] scraped {len(results)} topics")
        return results
    except Exception as e:
        print(f"  [zhihu] error: {e}")
        return []


def scrape_all() -> list[dict]:
    with httpx.Client(follow_redirects=True) as client:
        weibo = scrape_weibo(client)
        zhihu = scrape_zhihu(client)

    all_topics = weibo + zhihu

    seen_titles = set()
    deduped = []
    for t in all_topics:
        key = t["title"].lower().replace(" ", "")
        if key not in seen_titles:
            seen_titles.add(key)
            deduped.append(t)

    print(f"  [total] {len(deduped)} unique topics after dedup")
    return deduped
