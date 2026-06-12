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
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_MODEL_PRO, BLOG_CONTENT_DIR,
    setup_logging, get_logger, RUN_ID,
)
from censor import censor_events
from scorer import score_and_select
from analyzer import analyze_event
from article import generate_article
from schema import WeeklyIssue, WeeklySynthesis
from synthesizer import synthesize_events
from utils import get_week_id, get_week_range, retry_call, is_quality

logger = get_logger("pipeline")


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    setup_logging(verbose=args.verbose)
    logger.info("Run %s started", RUN_ID)

    phase_start: dict[str, float] = {}

    def _phase_begin(name: str):
        phase_start[name] = time.time()

    def _phase_done(name: str):
        elapsed = time.time() - phase_start.get(name, time.time())
        logger.info("[%s] 耗时 %.1fs", name, elapsed)

    flash_client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL)
    pro_client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_PRO, thinking=True)

    # Phase 0: Scrape REAL hot topics from actual platforms
    _phase_begin("Phase 0")
    logger.info("[Phase 0] 抓取真实热点数据...")

    if args.skip_scrape:
        raw_topics = []
        logger.info("  --skip-scrape: 跳过抓取")
    else:
        raw_topics = scrape_weibo_hot() + scrape_zhihu_hot() + scrape_hackernews_top()
    logger.info("  抓取到 %d 个话题（微博+知乎+HN）", len(raw_topics))

    if not raw_topics:
        cached = load_cache()
        if cached:
            logger.info("  抓取全失败，使用缓存数据（%d 个话题）", len(cached))
            raw_events = cached
        else:
            logger.critical("  抓取失败且无缓存，退出。请检查网络。")
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
        logger.info("  去重后: %d 个话题", len(raw_topics))

        # Convert to event format for pipeline
        raw_events = [
            {"title": t.title, "summary": f"{t.summary}\n来源: {t.url}"}
            for t in raw_topics
        ]
        save_cache(raw_events)
    _phase_done("Phase 0")

    # Phase 1: Political review
    _phase_begin("Phase 1")
    logger.info("[Phase 1] 政审过滤...")
    passed = retry_call(censor_events, flash_client, raw_events, phase="Phase 1")
    logger.info("  通过审查: %d 个", len(passed))
    _phase_done("Phase 1")

    # Phase 2: AI scoring and selection
    _phase_begin("Phase 2")
    logger.info("[Phase 2] AI 评分筛选...")
    selected = retry_call(score_and_select, flash_client, passed, top_n=args.max_events, phase="Phase 2")
    logger.info("  入选: %d 个", len(selected))
    _phase_done("Phase 2")

    # Phase 3: Per-event deep analysis (parallel, max 3 workers)
    _phase_begin("Phase 3")
    logger.info("[Phase 3] 逐事件深度梳理...")

    def _analyze_one(idx: int, event: dict) -> tuple[int, dict | None]:
        """搜索 + 分析单个事件，返回 (idx, result_or_None)。"""
        logger.info("  搜索 (%d): %s", idx, event['title'])
        search_results = search_event(event["title"], max_results=10)
        logger.info("    (%d) 找到 %d 条结果", idx, len(search_results))

        for attempt in range(2):
            try:
                result = analyze_event(pro_client, event, search_results, idx=idx)
                logger.info("    (%d) 分析完成", idx)
                return (idx, result)
            except Exception as e:
                if attempt < 1:
                    wait = min(2 ** (attempt + 1), 30) + random.uniform(0, 2)
                    logger.warning("    (%d) 分析失败: %s，等待%.0fs后重试...", idx, e, wait)
                    time.sleep(wait)
                else:
                    logger.warning("    (%d) 重试仍失败: %s，跳过此事件", idx, e)
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
        logger.critical("  没有事件通过分析，退出。")
        sys.exit(1)

    quality_events = [e for e in analyzed_events if is_quality(e)]
    dropped = len(analyzed_events) - len(quality_events)
    if dropped > 0:
        logger.info("  质量筛选: 剔除了 %d 个证据不足或内容空洞的事件", dropped)
    logger.info("  最终入选: %d 个", len(quality_events))
    _phase_done("Phase 3")

    if not quality_events:
        logger.critical("  质量筛选后没有事件留存，退出。")
        sys.exit(1)

    # Phase 4: Cross-event synthesis
    _phase_begin("Phase 4")
    logger.info("[Phase 4] 跨事件综合梳理...")
    synthesis = None
    if len(quality_events) >= 2:
        try:
            synthesis_result = synthesize_events(pro_client, quality_events)
            synthesis = WeeklySynthesis(**synthesis_result)
            logger.info("  完成：%d 主题, %d 趋势, %d 矛盾",
                len(synthesis.crossCuttingThemes),
                len(synthesis.trends),
                len(synthesis.contradictionsInMotion))
        except Exception as e:
            logger.warning("  [Phase 4] 失败: %s，跳过综合梳理", e)
    else:
        logger.info("  [Phase 4] 事件不足 2 个，跳过综合梳理")
    _phase_done("Phase 4")

    if args.dry_run:
        total_cost = flash_client.total_cost + pro_client.total_cost
        logger.info("Dry run complete. 共 %d 个事件，预估费用 $%.4f", len(quality_events), total_cost)
        return

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
    logger.info("输出: %s", json_path)
    logger.info("文章: %s", article_path)
    logger.info("共 %d 个事件", len(quality_events))
    logger.info("API 费用: $%.4f", total_cost)


def parse_args(argv: list[str] | None = None) -> "argparse.Namespace":
    import argparse
    parser = argparse.ArgumentParser(
        description="每周热点深度分析 — AI 驱动的热点事件分析工具",
    )
    parser.add_argument("--dry-run", action="store_true",
        help="运行流水线但不写入输出文件")
    parser.add_argument("--verbose", "-v", action="store_true",
        help="启用 DEBUG 级别日志")
    parser.add_argument("--skip-scrape", action="store_true",
        help="跳过 Phase 0 抓取，仅用缓存（用于重复测试）")
    parser.add_argument("--max-events", type=int, default=8,
        help="最大入选事件数（默认 8）")
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
