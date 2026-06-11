import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from chinese_scraper_utils import (
    DeepSeekClient,
    scrape_weibo_hot,
    scrape_zhihu_hot,
    scrape_hackernews_top,
)
from search import search_event

from cache import save_cache, load_cache
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_MODEL_PRO, BLOG_CONTENT_DIR
from censor import censor_events
from scorer import score_and_select
from analyzer import analyze_event
from article import generate_article
from schema import WeeklyIssue, WeeklySynthesis
from synthesizer import synthesize_events


def get_week_id() -> str:
    today = datetime.now()
    iso = today.isocalendar()
    return f"{today.year}-W{iso.week:02d}"


def get_week_range() -> tuple[str, str]:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def _retry_call(fn, *args, phase: str = "", max_retries: int = 2, **kwargs):
    """带退避重试的调用封装。"""
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt + random.uniform(0, 1)
                print(f"  [{phase}] 失败: {e}，{wait:.0f}s 后重试...")
                time.sleep(wait)
            else:
                raise


def main():
    flash_client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL)
    pro_client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_PRO, thinking=True)

    # Phase 0: Scrape REAL hot topics from actual platforms
    print("[Phase 0] 抓取真实热点数据...")
    raw_topics = scrape_weibo_hot() + scrape_zhihu_hot() + scrape_hackernews_top()
    print(f"  抓取到 {len(raw_topics)} 个话题（微博+知乎+HN）")

    if not raw_topics:
        cached = load_cache()
        if cached:
            print(f"  抓取全失败，使用缓存数据（{len(cached)} 个话题）")
            raw_events = cached
        else:
            print("  抓取失败且无缓存，退出。请检查网络。")
            sys.exit(1)
    else:
        raw_events = None  # will be set below after dedup

    if raw_topics:
        # Deduplicate topics by title
        seen = set()
        deduped = []
        for t in raw_topics:
            key = t.title.lower().replace(" ", "")
            if key not in seen:
                seen.add(key)
                deduped.append(t)
        raw_topics = deduped
        print(f"  去重后: {len(raw_topics)} 个话题")

        # Convert to event format for pipeline
        raw_events = [
            {"title": t.title, "summary": f"{t.summary}\n来源: {t.url}"}
            for t in raw_topics
        ]
        save_cache(raw_events)

    # Phase 1: Political review
    print("[Phase 1] 政审过滤...")
    passed = _retry_call(censor_events, flash_client, raw_events, phase="Phase 1")
    print(f"  通过审查: {len(passed)} 个")

    # Phase 2: AI scoring and selection
    print("[Phase 2] AI 评分筛选...")
    selected = _retry_call(score_and_select, flash_client, passed, top_n=8, phase="Phase 2")
    print(f"  入选: {len(selected)} 个")

    # Phase 3: Per-event deep analysis (parallel, max 3 workers)
    print("[Phase 3] 逐事件深度梳理...")

    def _analyze_one(idx: int, event: dict) -> tuple[int, dict | None]:
        """搜索 + 分析单个事件，返回 (idx, result_or_None)。"""
        print(f"  搜索 ({idx}): {event['title']}")
        search_results = search_event(event["title"], max_results=10)
        print(f"    ({idx}) 找到 {len(search_results)} 条结果")

        for attempt in range(2):
            try:
                result = analyze_event(pro_client, event, search_results, idx=idx)
                print(f"    ({idx}) 分析完成")
                return (idx, result)
            except Exception as e:
                if attempt < 1:
                    wait = min(2 ** (attempt + 1), 30) + random.uniform(0, 2)
                    print(f"    ({idx}) 分析失败: {e}，等待{wait:.0f}s后重试...")
                    time.sleep(wait)
                else:
                    print(f"    ({idx}) 重试仍失败: {e}，跳过此事件")
                    return (idx, None)

    results_map: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(_analyze_one, i + 1, event): i + 1
            for i, event in enumerate(selected)
        }
        for fut in as_completed(futures):
            idx, result = fut.result()
            if result is not None:
                results_map[idx] = result

    analyzed_events = [results_map[i] for i in sorted(results_map)]

    if not analyzed_events:
        print("  没有事件通过分析，退出。")
        sys.exit(1)

    # Quality gate: events must have real substance
    def is_quality(event):
        timeline = event.get("timeline", [])
        evidence = event.get("evidence", [])
        if len(timeline) < 3:
            return False
        if len(evidence) < 2:
            return False
        verified = [e for e in evidence if e.get("authenticity") in ("真实", "存疑")]
        if len(verified) == 0:
            return False
        if len(event.get("dialecticalSummary", "")) < 30:
            return False
        return True

    quality_events = [e for e in analyzed_events if is_quality(e)]
    dropped = len(analyzed_events) - len(quality_events)
    if dropped > 0:
        print(f"  质量筛选: 剔除了 {dropped} 个证据不足或内容空洞的事件")
    print(f"  最终入选: {len(quality_events)} 个")

    if not quality_events:
        print("  质量筛选后没有事件留存，退出。")
        sys.exit(1)

    # Phase 4: Cross-event synthesis
    print("[Phase 4] 跨事件综合梳理...")
    synthesis = None
    if len(quality_events) >= 2:
        try:
            synthesis_result = synthesize_events(pro_client, quality_events)
            synthesis = WeeklySynthesis(**synthesis_result)
            print(f"  完成：{len(synthesis.crossCuttingThemes)} 主题, {len(synthesis.trends)} 趋势, {len(synthesis.contradictionsInMotion)} 矛盾")
        except Exception as e:
            print(f"  [Phase 4] 失败: {e}，跳过综合梳理")
    else:
        print("  [Phase 4] 事件不足 2 个，跳过综合梳理")

    week_id = get_week_id()
    week_start, week_end = get_week_range()

    issue = WeeklyIssue(
        id=week_id,
        weekStart=week_start,
        weekEnd=week_end,
        events=quality_events,
        synthesis=synthesis,
    )

    BLOG_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # JSON output
    json_path = BLOG_CONTENT_DIR / f"{week_id}.json"
    json_path.write_text(
        issue.model_dump_json(indent=2, ensure_ascii=False, by_alias=True),
        encoding="utf-8",
    )

    # Markdown article output (blog posts directory)
    blog_root = BLOG_CONTENT_DIR.parent  # src/content
    posts_dir = blog_root / "posts" / week_id
    posts_dir.mkdir(parents=True, exist_ok=True)
    article_path = posts_dir / "index.md"
    md = generate_article(issue, blog_root)
    article_path.write_text(md, encoding="utf-8")

    total_cost = flash_client.total_cost + pro_client.total_cost
    print(f"\n输出: {json_path}")
    print(f"文章: {article_path}")
    print(f"共 {len(quality_events)} 个事件")
    print(f"API 费用: ${total_cost:.4f}")


if __name__ == "__main__":
    main()
