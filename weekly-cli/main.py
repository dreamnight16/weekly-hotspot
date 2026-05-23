import sys
import time
from datetime import datetime, timedelta
from config import DEEPSEEK_API_KEY, BLOG_CONTENT_DIR
from client import DeepSeekClient
from censor import censor_events
from scorer import score_and_select
from analyzer import analyze_event
from scraper import scrape_all
from searcher import search_event
from schema import WeeklyIssue


def get_week_id() -> str:
    today = datetime.now()
    iso = today.isocalendar()
    return f"{today.year}-W{iso.week:02d}"


def get_week_range() -> tuple[str, str]:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def main():
    client = DeepSeekClient(DEEPSEEK_API_KEY)

    # Phase 0: Scrape REAL hot topics from actual platforms
    print("[Phase 0] 抓取真实热点数据...")
    raw_topics = scrape_all()
    print(f"  抓取到 {len(raw_topics)} 个话题（微博+知乎+HN）")

    if not raw_topics:
        print("  抓取失败，退出。请检查网络或 API 可用性。")
        sys.exit(1)

    # Convert to event format for pipeline
    raw_events = [
        {"title": t["title"], "summary": f"{t['summary']}\n来源: {t['url']}"}
        for t in raw_topics
    ]

    # Phase 1: Political review
    print("[Phase 1] 政审过滤...")
    passed = censor_events(client, raw_events)
    print(f"  通过审查: {len(passed)} 个")

    # Phase 2: AI scoring and selection
    print("[Phase 2] AI 评分筛选...")
    selected = score_and_select(client, passed, top_n=8)
    print(f"  入选: {len(selected)} 个")

    # Phase 3: Per-event deep analysis
    print("[Phase 3] 逐事件深度梳理...")
    analyzed_events = []
    for i, event in enumerate(selected):
        print(f"  分析 ({i+1}/{len(selected)}): {event['title']}")
        # Search web for real info on this event
        print(f"    搜索中...")
        search_results = search_event(event["title"])
        print(f"    找到 {len(search_results)} 条结果")

        try:
            result = analyze_event(client, event, search_results, idx=i + 1)
            analyzed_events.append(result)
        except Exception as e:
            print(f"    分析失败: {e}，等待3秒后重试...")
            time.sleep(3)
            try:
                result = analyze_event(client, event, search_results, idx=i + 1)
                analyzed_events.append(result)
            except Exception as e2:
                print(f"    重试仍失败: {e2}，跳过此事件")

    if not analyzed_events:
        print("  没有事件通过分析，退出。")
        sys.exit(1)

    # Quality gate: events must have real substance
    def is_quality(event):
        timeline = event.get("timeline", [])
        evidence = event.get("evidence", [])
        # Need enough timeline nodes and evidence
        if len(timeline) < 3:
            return False
        if len(evidence) < 2:
            return False
        # At least some evidence must be verifiable (not all 待验证/不实)
        verified = [e for e in evidence if e.get("authenticity") in ("真实", "存疑")]
        if len(verified) == 0:
            return False
        # Summary must have substance
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

    week_id = get_week_id()
    week_start, week_end = get_week_range()

    issue = WeeklyIssue(
        id=week_id,
        weekStart=week_start,
        weekEnd=week_end,
        events=quality_events,
    )

    BLOG_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BLOG_CONTENT_DIR / f"{week_id}.json"
    output_path.write_text(
        issue.model_dump_json(indent=2, ensure_ascii=False, by_alias=True),
        encoding="utf-8",
    )

    print(f"\n输出: {output_path}")
    print(f"共 {len(quality_events)} 个事件")


if __name__ == "__main__":
    main()
