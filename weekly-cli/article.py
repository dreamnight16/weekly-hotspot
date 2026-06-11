"""生成 Markdown 周刊文章。

风格定位：说人话、打比方、有态度。参考毛选「用老百姓的话讲大道理」的传统，
融合现代短段落节奏，保持马列毛主义阶级分析的严谨性。

核心原则：
- 每一段分析背后都是真实的物质利益，不贴标签
- 用日常语言讲清楚「谁得到了什么、谁失去了什么」
- 短句有呼吸感，长句有重量感
- 有态度但不喊口号，尖锐但不刻薄
"""
import json
from datetime import datetime
from pathlib import Path


WEEKDAY_ZH = ["一", "二", "三", "四", "五", "六", "日"]


def _format_date_range(start: str, end: str) -> str:
    """格式化日期范围为中文。"""
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        return f"{s.month}月{s.day}日（周{WEEKDAY_ZH[s.weekday()]}）— {e.month}月{e.day}日（周{WEEKDAY_ZH[e.weekday()]}）"
    except Exception:
        return f"{start} — {end}"


def _tagline(events: list[dict]) -> str:
    """根据本周事件内容生成一句引语。"""
    n = len(events)
    scores = [e.get("impactScore", 1) for e in events]
    avg = sum(scores) / n if n else 0
    if avg >= 4:
        intensity = "密集"
    elif avg >= 3:
        intensity = "值得关注"
    else:
        intensity = "相对平静"
    return f"本周 {n} 个事件，信号{intensity}。"


def load_last_week(blog_dir: Path, this_week_id: str) -> dict | None:
    """加载上周的周刊 JSON。"""
    try:
        year, w = this_week_id.split("-W")
        week_num = int(w)
        year_num = int(year)
        if week_num > 1:
            last_id = f"{year_num}-W{week_num - 1:02d}"
        else:
            last_id = f"{year_num - 1}-W52"
        last_path = blog_dir / "src" / "content" / "weekly" / f"{last_id}.json"
        if not last_path.exists():
            return None
        return json.loads(last_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _event_block(event: dict, idx: int) -> str:
    """单个事件的分析——说人话，讲清楚利益格局。"""
    ca = event.get("classAnalysis", {})
    evidence = event.get("evidence", [])
    timeline = event.get("timeline", [])
    edges = event.get("edges", [])

    title = event["title"]
    summary = event.get("summary", "")
    impact = event.get("impactScore", 1)
    info_gain = event.get("infoGainScore", 1)
    dialectical = event.get("dialecticalSummary", "")

    # 影响力描述
    impact_words = {5: "冲击力极强", 4: "冲击力强", 3: "冲击力中等", 2: "冲击力一般", 1: "冲击力较弱"}
    info_words = {5: "信息量大", 4: "信息量较大", 3: "信息量中等", 2: "信息量较小", 1: "信息量少"}

    lines = [
        f"## {idx}. {title}",
        "",
        f"*{impact_words.get(impact, '')} · {info_words.get(info_gain, '')}*",
        "",
        summary,
        "",
    ]

    # 阶级分析 —— 用白话讲
    if ca:
        class_nature = ca.get("classNature", "")
        contradiction = ca.get("contradiction", "")
        context = ca.get("historicalContext", "")

        if class_nature:
            lines.append(f"**谁得了什么、谁失了什么？**")
            lines.append("")
            lines.append(class_nature)
            lines.append("")

        if contradiction:
            lines.append(f"**矛盾在哪？**")
            lines.append("")
            lines.append(contradiction)
            lines.append("")

        if context:
            lines.append(f"**这件事从哪来、往哪去？**")
            lines.append("")
            lines.append(context)
            lines.append("")

    # 辩证总结
    if dialectical:
        lines.append(f"**一句话**：{dialectical}")
        lines.append("")

    # 时间线 —— 讲故事
    if timeline:
        lines.append("### 怎么发展的")
        lines.append("")
        for node in timeline:
            t = node.get("time", "")
            if len(t) >= 10:
                t = t[:10]
            lines.append(f"- **{t}** — {node['title']}：{node['description']}")
        lines.append("")

    # 证据 —— 关键信源
    if evidence:
        lines.append("### 信源")
        lines.append("")
        real = [e for e in evidence if e.get("authenticity") == "真实"]
        dubious = [e for e in evidence if e.get("authenticity") in ("存疑", "待验证")]
        if real:
            lines.append("**可确认的**：")
            for ev in real:
                source = ev.get("sourceName", "未知来源")
                lines.append(f"- {source}（{ev.get('sourceType', '')}）：{ev.get('content', '')}")
            lines.append("")
        if dubious:
            lines.append("**待验证的**：")
            for ev in dubious:
                source = ev.get("sourceName", "未知来源")
                reason = ev.get("aiReason", "")
                lines.append(f"- {source}：{ev.get('content', '')}（*{reason}*）")
            lines.append("")

    # 关系 —— 因果脉络
    if edges:
        lines.append("### 脉络")
        lines.append("")
        for edge in edges:
            arrow = "→" if edge["type"] == "因果" else ("↔" if edge["type"] == "关联" else "⇄")
            lines.append(f"- **{edge['from']}** {arrow} **{edge['to']}**（{edge['type']}）")
            if edge.get("description"):
                lines.append(f"  {edge['description']}")
        lines.append("")

    return "\n".join(lines)


def _synthesis_narrative(synthesis: dict, event_titles: list[str]) -> str:
    """把综合综述变成可读的叙事——不是说教，是讲故事。"""
    narrative = synthesis.get("weeklyNarrative", "")
    themes = synthesis.get("crossCuttingThemes", [])
    trends = synthesis.get("trends", [])
    contradictions = synthesis.get("contradictionsInMotion", [])
    assessment = synthesis.get("globalAssessment", "")
    gaps = synthesis.get("dataGaps", [])

    lines = ["## 一、这周发生了什么", ""]

    if narrative:
        lines.append(narrative)
        lines.append("")

    if themes:
        lines.append("## 二、不止一件事——几条共同的线索")
        lines.append("")
        for t in themes:
            eids = "、".join(t.get("relatedEventIds", []))
            lines.append(f"**{t['name']}**（涉及 {eids}）")
            lines.append("")
            lines.append(t["description"])
            lines.append("")
            if t.get("significance"):
                lines.append(f"这件事之所以值得注意，是因为：{t['significance']}")
                lines.append("")

    if trends:
        lines.append("## 三、风向在变")
        lines.append("")
        for t in trends:
            direction = t.get("direction", "")
            if direction == "上升":
                verb = "——在上升。"
            elif direction == "下降":
                verb = "——在下降。"
            elif direction == "激化":
                verb = "——在加剧。"
            elif direction == "缓和":
                verb = "——在缓和。"
            else:
                verb = "。"
            lines.append(f"**{t['name']}**{verb}{t['description']}")
            lines.append("")

    if contradictions:
        lines.append("## 四、底层的矛盾在怎么动")
        lines.append("")
        for c in contradictions:
            state = c.get("currentState", "")
            lines.append(f"**{c['contradiction']}**")
            lines.append("")
            lines.append(f"目前处在{state}的状态。{c['opposingForces']}")
            lines.append("")
            if c.get("outlook"):
                lines.append(f"判断：{c['outlook']}")
                lines.append("")

    if assessment:
        lines.append("## 五、总的来看")
        lines.append("")
        lines.append(assessment)
        lines.append("")

    if gaps:
        lines.append("### 还没看清楚的地方")
        lines.append("")
        for g in gaps:
            lines.append(f"- {g}")
        lines.append("")

    return "\n".join(lines)


def _diff_section(this_synthesis: dict, last_week: dict) -> str:
    """上周对比——看看变化的方向。"""
    last_syn = last_week.get("synthesis")
    if not last_syn:
        last_events = last_week.get("events", [])
        if not last_events:
            return ""
        last_themes = [e.get("title", "")[:20] for e in last_events[:3]]
        last_summary = f"上周主要关注了：{'、'.join(last_themes)}等 {len(last_events)} 个事件。"
    else:
        last_narrative = last_syn.get("weeklyNarrative", "")[:300]
        last_themes = [t["name"] for t in last_syn.get("crossCuttingThemes", [])]
        last_summary = last_narrative
        if last_themes:
            last_summary += f"\n\n上周主题：{'、'.join(last_themes)}"

    this_themes = [t["name"] for t in this_synthesis.get("crossCuttingThemes", [])]

    lines = [
        "## 六、跟上周比",
        "",
        "### 上周回顾",
        "",
        last_summary,
        "",
    ]
    if this_themes:
        new_themes = [t for t in this_themes if not any(
            t in lt for lt in last_themes
        )]
        continuing = [t for t in this_themes if any(
            t in lt for lt in last_themes
        )]
        if new_themes:
            lines.append(f"**新出现的**：{'、'.join(new_themes)}")
            lines.append("")
        if continuing:
            lines.append(f"**在延续的**：{'、'.join(continuing)}")
            lines.append("")

    return "\n".join(lines)


def generate_article(
    issue: "WeeklyIssue",  # noqa: F821
    blog_dir: Path,
) -> str:
    """生成周刊文章——有态度、说人话、讲道理。"""
    events = [
        e.model_dump(by_alias=True) if hasattr(e, "model_dump") else e
        for e in issue.events
    ]
    synthesis = (
        issue.synthesis.model_dump()
        if (issue.synthesis and hasattr(issue.synthesis, "model_dump"))
        else None
    )

    date_range = _format_date_range(issue.weekStart, issue.weekEnd)
    tagline = _tagline(events)

    # 从事件标题提取关键词做标签
    keywords = ["热点", "周刊", "分析"]
    for e in events:
        for w in e["title"][:20].replace("，", " ").replace("、", " ").split():
            if len(w) >= 2 and w not in keywords:
                keywords.append(w)
    if synthesis:
        for t in synthesis.get("crossCuttingThemes", [])[:2]:
            if t["name"] not in keywords:
                keywords.insert(3, t["name"])

    # 根据内容生成描述
    event_count = len(events)
    if synthesis:
        desc = synthesis.get("weeklyNarrative", "")[:120].replace("\n", " ")
    else:
        sample_titles = "、".join(e["title"][:15] for e in events[:3])
        desc = f"本周（{issue.weekStart} 至 {issue.weekEnd}）热点事件阶级分析，涵盖 {sample_titles}等 {event_count} 个事件。"
    if len(desc) > 150:
        desc = desc[:147] + "..."

    lines = [
        "---",
        f'title: 每周热点分析 {issue.id}',
        f"published: {issue.weekEnd}",
        f"description: {desc}",
        "category: 周刊",
        f"tags: [{', '.join(keywords[:8])}]",
        "---",
        "",
        f"# 每周热点分析 {issue.id}",
        "",
        f"> {date_range}　|　{tagline}",
        "",
    ]

    # 综合综述部分（如果有 synthesis）
    last_week = load_last_week(blog_dir, issue.id) if synthesis else None

    if synthesis:
        event_titles = [e["title"] for e in events]
        lines.append(_synthesis_narrative(synthesis, event_titles))
        lines.append("")

        # 上周对比
        if last_week:
            diff = _diff_section(synthesis, last_week)
            if diff:
                lines.append(diff)
                lines.append("")

    # 逐事件分析 —— 动态确定章节编号
    syn_sections = 1  # 一、这周发生了什么
    if synthesis:
        if synthesis.get("crossCuttingThemes"):
            syn_sections += 1
        if synthesis.get("trends"):
            syn_sections += 1
        if synthesis.get("contradictionsInMotion"):
            syn_sections += 1
        if synthesis.get("globalAssessment"):
            syn_sections += 1
        if last_week and last_week.get("synthesis"):
            syn_sections += 1  # N、跟上周比
    section_num = syn_sections + 1
    lines.append(f"## {_section_label(section_num)}、逐件看")
    lines.append("")
    for i, event in enumerate(events):
        lines.append(_event_block(event, i + 1))
        lines.append("---")
        lines.append("")

    # 尾注
    lines.append(
        "*本文由 [weekly-hotspot](https://github.com/sixtdreanight/weekly-hotspot) "
        "分析系统自动生成，数据来自微博、知乎、Hacker News 实时热点。"
        "每期周刊基于 DeepSeek 模型进行马列毛主义阶级分析，"
        "力求在真实信息的基础上，讲清楚每件事背后的物质利益格局。*\n"
    )

    return "\n".join(lines)


def _section_label(n: int) -> str:
    """数字转中文序号。"""
    labels = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if n < len(labels):
        return labels[n]
    return str(n)
