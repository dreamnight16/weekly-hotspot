import sys
from datetime import datetime, timedelta
from config import DEEPSEEK_API_KEY, BLOG_CONTENT_DIR
from client import DeepSeekClient
from censor import censor_events
from scorer import score_and_select
from analyzer import analyze_event
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


def fetch_weekly_hotspots(client: DeepSeekClient) -> list[dict]:
    result = client.chat_json([
        {"role": "system", "content": "你是一个新闻聚合助手。请搜索并列出本周（过去7天内）的热点新闻事件。对每个事件提供标题和一句话摘要。重点关注科技、社会、经济、国际领域。返回至少20个事件。返回格式：{\"events\": [{\"title\": \"...\", \"summary\": \"...\"}]}"},
        {"role": "user", "content": "请列出本周的热点事件，至少20个。重点关注有实际影响的事件，排除纯娱乐八卦。"},
    ])
    return result.get("events", [])


def main():
    client = DeepSeekClient(DEEPSEEK_API_KEY)

    print("[Phase 0] 获取本周热点候选...")
    raw_events = fetch_weekly_hotspots(client)
    print(f"  获取到 {len(raw_events)} 个候选事件")

    print("[Phase 0] 政审过滤...")
    passed = censor_events(client, raw_events)
    print(f"  通过审查: {len(passed)} 个")

    print("[Phase 1] AI 评分筛选...")
    selected = score_and_select(client, passed, top_n=8)
    print(f"  入选: {len(selected)} 个")

    print("[Phase 2] 逐事件深度梳理...")
    analyzed_events = []
    for i, event in enumerate(selected):
        print(f"  分析 ({i+1}/{len(selected)}): {event['title']}")
        try:
            result = analyze_event(client, event, idx=i + 1)
            analyzed_events.append(result)
        except Exception as e:
            print(f"    分析失败: {e}，重试一次...")
            try:
                result = analyze_event(client, event, idx=i + 1)
                analyzed_events.append(result)
            except Exception as e2:
                print(f"    重试仍失败: {e2}，跳过此事件")

    week_id = get_week_id()
    week_start, week_end = get_week_range()

    issue = WeeklyIssue(
        id=week_id,
        weekStart=week_start,
        weekEnd=week_end,
        events=analyzed_events,
    )

    BLOG_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BLOG_CONTENT_DIR / f"{week_id}.json"
    output_path.write_text(issue.model_dump_json(indent=2, ensure_ascii=False, by_alias=True), encoding="utf-8")

    print(f"\n输出: {output_path}")
    print(f"共 {len(analyzed_events)} 个事件")


if __name__ == "__main__":
    main()
