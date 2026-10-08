"""Generate Markdown weekly article from a WeeklyIssue analysis.

The article is organized by the five-phase dialectical epistemological movement:
  一、现象 — Phenomenon Grasping (empirical)
  二、矛盾 — Contradiction Identification (analysis)
  三、展开 — Dialectical Unfolding (theory)
  四、定位 — Historical Positioning (context)
  五、方向 — Practice Orientation (action)

Core principles:
  - Each phase section renders the key fields from the corresponding phase model.
  - Missing phases are skipped gracefully (phase2=None → no section).
  - Uncertainty labels [HIGH]/[MEDIUM]/[LOW] annotate analytical assertions.
  - Footer references 格物 (Dianalyze) with a GitHub link.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from schema import (
        ContradictionIdentification,
        DialecticalUnfolding,
        GDELTBaseline,
        HistoricalPositioning,
        NineDimScores,
        PhenomenonGrasping,
        PracticeOrientation,
        SelectedEvent,
        WeeklyIssue,
    )

WEEKDAY_ZH = ["一", "二", "三", "四", "五", "六", "日"]

CONFIDENCE_LABELS = {
    "HIGH": " [HIGH]",
    "MEDIUM": " [MEDIUM]",
    "LOW": " [LOW]",
}


# =============================================================================
# Utility functions (retained from v1 article.py)
# =============================================================================


def _format_date_range(start: str, end: str) -> str:
    """Format a date range as Chinese text."""
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        return (
            f"{s.month}月{s.day}日（周{WEEKDAY_ZH[s.weekday()]}）"
            f"— {e.month}月{e.day}日（周{WEEKDAY_ZH[e.weekday()]}）"
        )
    except Exception:
        return f"{start} — {end}"


def _tagline(events: list[SelectedEvent]) -> str:
    """Generate a one-line signal-intensiry summary based on event count."""
    n = len(events)
    if n >= 8:
        intensity = "高度密集"
    elif n >= 5:
        intensity = "较密集"
    elif n >= 3:
        intensity = "值得关注"
    else:
        intensity = "相对平静"
    return f"本周收录 {n} 个事件，信号{intensity}。"


def _confidence_label(confidence: Optional[str]) -> str:
    """Return a [HIGH]/[MEDIUM]/[LOW] label, or empty string."""
    if not confidence:
        return ""
    return CONFIDENCE_LABELS.get(confidence.upper(), "")


# =============================================================================
# Phase section renderers
# =============================================================================


def _render_phase1(phase: PhenomenonGrasping) -> str:
    """Render Phase 1: 现象把握 — empirical event collection."""
    lines: list[str] = []
    lines.append("## 一、现象")
    lines.append("")

    if phase.phaseSummary:
        lines.append(phase.phaseSummary)
        lines.append("")

    if phase.gdeltBaseline:
        lines.append("### 数据基线")
        lines.append("")
        lines.extend(_render_gdelt_baseline(phase.gdeltBaseline))
        lines.append("")

    if phase.sourceQualityReport:
        lines.append("### 信源质量")
        lines.append("")
        lines.append(phase.sourceQualityReport)
        lines.append("")

    selected = phase.selectedEvents
    if selected:
        lines.append(f"### 入选事件（{len(selected)}）")
        lines.append("")
        for e in selected:
            lines.append(f"- **{e.title}**")
            if e.summary:
                lines.append(f"  {e.summary}")
            if e.materialContent:
                lines.append(f"  *物质内容：{e.materialContent}*")
            if e.isDirectExpression:
                lines.append("  *直接表现*")
            if e.sourceUrl:
                lines.append(f"  来源：{e.sourceUrl}")
        lines.append("")

    excluded = phase.excludedEvents
    if excluded:
        lines.append(f"### 排除事件（{len(excluded)}）")
        lines.append("")
        for e in excluded:
            lines.append(f"- **{e.title}**")
            if e.exclusionReason:
                lines.append(f"  *排除原因：{e.exclusionReason}*")
        lines.append("")

    return "\n".join(lines)


def _render_gdelt_baseline(baseline: GDELTBaseline) -> list[str]:
    """Render GDELT baseline statistics."""
    return [
        f"- 总文章数：{baseline.totalArticles:,}",
        f"- 平均语调：{baseline.avgTone:+.2f}",
        f"- 事件数：{baseline.numEvents:,}",
        f"- 时间段：{baseline.period}" if baseline.period else "",
    ]


def _render_phase2(phase: ContradictionIdentification) -> str:
    """Render Phase 2: 矛盾识别 — interest and class analysis."""
    lines: list[str] = []
    lines.append("## 二、矛盾")
    lines.append("")

    if phase.phaseSummary:
        lines.append(phase.phaseSummary)
        lines.append("")

    if phase.overallContradictionLandscape:
        lines.append("### 矛盾格局")
        lines.append("")
        lines.append(phase.overallContradictionLandscape)
        lines.append("")

    if phase.interestStructures:
        lines.append("### 利益结构")
        lines.append("")
        for i, s in enumerate(phase.interestStructures, 1):
            intensity_bars = "█" * s.intensity + "░" * (5 - s.intensity)
            lines.append(f"**{i}. {s.interestGroup}**  [{intensity_bars}]")
            lines.append("")
            if s.materialInterest:
                lines.append(f"物质利益：{s.materialInterest}")
                lines.append("")
            if s.expressionForm:
                lines.append(f"表现形式：{s.expressionForm}")
                lines.append("")
        lines.append("")

    if phase.classPositions:
        lines.append("### 阶级立场")
        lines.append("")
        for i, c in enumerate(phase.classPositions, 1):
            lines.append(f"**{i}. {c.className}**")
            lines.append("")
            if c.position:
                lines.append(f"生产关系位置：{c.position}")
            if c.coreInterest:
                lines.append(f"核心利益：{c.coreInterest}")
            if c.contradictions:
                lines.append(f"矛盾：{'、'.join(c.contradictions)}")
            lines.append("")
        lines.append("")

    if phase.nineDimScores:
        lines.append("### 九维评分")
        lines.append("")
        lines.extend(_render_nine_dim_scores(phase.nineDimScores))
        lines.append("")

    if phase.competingHypotheses:
        lines.append("### 竞争性假说")
        lines.append("")
        for h in phase.competingHypotheses:
            lines.append(f"- **{h.hypothesisId}**：{h.description}  "
                         f"*概率 {h.assessedProbability:.0%}*")
            if h.supportingEvidence:
                lines.append(f"  支持：{h.supportingEvidence}")
            if h.contradictingEvidence:
                lines.append(f"  反对：{h.contradictingEvidence}")
            lines.append("")
        lines.append("")

    return "\n".join(lines)


def _render_nine_dim_scores(scores: NineDimScores) -> list[str]:
    """Render nine-dimensional score table as Markdown list."""
    dims = [
        ("magnitude", "规模"),
        ("scope", "范围"),
        ("velocity", "速度"),
        ("novelty", "新颖度"),
        ("cascadePotential", "连锁潜力"),
        ("actorProminence", "主体显著度"),
        ("uncertainty", "不确定性"),
        ("polarity", "极化度"),
        ("durability", "持久度"),
    ]
    out_lines: list[str] = []
    for key, label in dims:
        score, confidence = getattr(scores, key, (5, 0.5))
        conf_label = ""
        if confidence >= 0.7:
            conf_label = " [HIGH]"
        elif confidence >= 0.4:
            conf_label = " [MEDIUM]"
        else:
            conf_label = " [LOW]"
        bar = "█" * score + "░" * (10 - score)
        out_lines.append(f"- **{label}**：{score}/10 [{bar}] `confidence={confidence:.2f}`{conf_label}")
    return out_lines


def _render_phase3(phase: DialecticalUnfolding) -> str:
    """Render Phase 3: 辩证展开 — dialectical unfolding."""
    lines: list[str] = []
    confidence_suffix = _confidence_label(phase.dialecticalConfidence)
    lines.append(f"## 三、展开{confidence_suffix}")
    lines.append("")

    if phase.phaseSummary:
        lines.append(phase.phaseSummary)
        lines.append("")

    if phase.unityOfOpposites:
        lines.append("### 对立统一")
        lines.append("")
        opp = phase.unityOfOpposites
        if opp.identity:
            lines.append(f"**同一性**：{opp.identity}")
            lines.append("")
        if opp.struggle:
            lines.append(f"**斗争性**：{opp.struggle}")
            lines.append("")
        if opp.particularity:
            lines.append(f"**特殊性**：{opp.particularity}")
            lines.append("")
        if opp.universality:
            lines.append(f"**普遍性**：{opp.universality}")
            lines.append("")

    if phase.quantityQuality:
        lines.append("### 量变质变")
        lines.append("")
        qq = phase.quantityQuality
        lines.append(f"当前阶段：**{qq.currentPhase}**")
        lines.append("")
        if qq.quantitativeDirection:
            lines.append(f"量变方向：{qq.quantitativeDirection}")
        if qq.measure:
            lines.append(f"度：{qq.measure}")
        if qq.oldQualityNegated:
            lines.append(f"被否定的旧质：{qq.oldQualityNegated}")
        if qq.newQuality:
            lines.append(f"新质：{qq.newQuality}")
        lines.append("")

    if phase.negationOfNegation:
        lines.append("### 否定之否定")
        lines.append("")
        non_ = phase.negationOfNegation
        if non_.oldThing:
            lines.append(f"旧事物：{non_.oldThing}")
        if non_.firstNegation:
            lines.append(f"第一次否定：{non_.firstNegation}")
        if non_.internalNegation:
            lines.append(f"内部否定：{non_.internalNegation}")
        if non_.direction:
            lines.append(f"发展方向：**{non_.direction}**")
        if non_.stageCharacteristics:
            lines.append(f"阶段特征：{non_.stageCharacteristics}")
        lines.append("")

    if phase.adversarialReview:
        lines.append("### 对抗审查")
        lines.append("")
        ar = phase.adversarialReview
        conf = _confidence_label(ar.confidence)
        if ar.originalClaim:
            lines.append(f"原主张：{ar.originalClaim}{conf}")
            lines.append("")
        if ar.critique:
            lines.append(f"批判：{ar.critique}")
            lines.append("")
        if ar.revisedClaim:
            lines.append(f"修正后主张：{ar.revisedClaim}")
            lines.append("")

    if phase.causalLoopDiagram:
        lines.append("### 因果循环")
        lines.append("")
        cld = phase.causalLoopDiagram
        if cld.description:
            lines.append(cld.description)
            lines.append("")
        if cld.nodes:
            lines.append(f"节点：{' → '.join(cld.nodes)}")
            lines.append("")
        if cld.positiveFeedbackLoops:
            lines.append(f"正反馈环：{'、'.join(cld.positiveFeedbackLoops)}")
            lines.append("")
        if cld.negativeFeedbackLoops:
            lines.append(f"负反馈环：{'、'.join(cld.negativeFeedbackLoops)}")
            lines.append("")
        if cld.keyLeveragePoints:
            lines.append(f"关键杠杆点：{'、'.join(cld.keyLeveragePoints)}")
            lines.append("")

    if phase.dataValidation:
        lines.append("### 数据验证")
        lines.append("")
        dv = phase.dataValidation
        conf = _confidence_label(dv.confidence)
        lines.append(f"验证项：{dv.validationCheck}{conf}")
        lines.append("")
        if dv.result:
            lines.append(f"结果：{dv.result}")
            lines.append("")
        if dv.issues:
            lines.append("问题：")
            for issue in dv.issues:
                lines.append(f"- {issue}")
            lines.append("")

    return "\n".join(lines)


def _render_phase4(phase: HistoricalPositioning) -> str:
    """Render Phase 4: 历史定位 — historical positioning."""
    lines: list[str] = []
    lines.append("## 四、定位")
    lines.append("")

    if phase.phaseSummary:
        lines.append(phase.phaseSummary)
        lines.append("")

    if phase.crossCuttingSynthesis:
        lines.append("### 交叉综合")
        lines.append("")
        lines.append(phase.crossCuttingSynthesis)
        lines.append("")

    if phase.epochThemes:
        lines.append("### 时代主题")
        lines.append("")
        for t in phase.epochThemes:
            lines.append(f"- **{t.themeName}**")
            if t.description:
                lines.append(f"  {t.description}")
            if t.relevanceToCurrentEvents:
                lines.append(f"  *与当前事件的关系：{t.relevanceToCurrentEvents}*")
            lines.append("")
        lines.append("")

    if phase.systemArchetypes:
        lines.append("### 系统原型")
        lines.append("")
        for a in phase.systemArchetypes:
            lines.append(f"- **{a.patternName}**（`{a.archetypeType}`）")
            if a.description:
                lines.append(f"  {a.description}")
            if a.structuralFeatures:
                lines.append(f"  *结构特征：{a.structuralFeatures}*")
            lines.append("")
        lines.append("")

    if phase.hiddenConnections:
        lines.append("### 隐藏关联")
        lines.append("")
        for c in phase.hiddenConnections:
            lines.append(f"- **{c.connectionName}**：{c.entityA} ↔ {c.entityB}")
            if c.connectionMechanism:
                lines.append(f"  机制：{c.connectionMechanism}")
            if c.significance:
                lines.append(f"  意义：{c.significance}")
            lines.append("")
        lines.append("")

    if phase.historicalAnalogies:
        lines.append("### 历史类比")
        lines.append("")
        for a in phase.historicalAnalogies:
            lines.append(f"- **{a.analogyName}**")
            if a.historicalPeriod:
                lines.append(f"  时期：{a.historicalPeriod}")
            if a.historicalEvent:
                lines.append(f"  事件：{a.historicalEvent}")
            if a.similarity:
                lines.append(f"  相似性：{a.similarity}")
            if a.difference:
                lines.append(f"  差异性：{a.difference}")
            if a.lessonForToday:
                lines.append(f"  今鉴：{a.lessonForToday}")
            lines.append("")
        lines.append("")

    return "\n".join(lines)


def _render_phase5(phase: PracticeOrientation) -> str:
    """Render Phase 5: 实践导向 — practice orientation."""
    lines: list[str] = []
    lines.append("## 五、方向")
    lines.append("")

    if phase.overallJudgment:
        lines.append(phase.overallJudgment)
        lines.append("")

    if phase.practiceSignificance:
        lines.append("### 实践意义")
        lines.append("")
        lines.append(phase.practiceSignificance)
        lines.append("")

    if phase.scenarios:
        lines.append("### 前瞻情景")
        lines.append("")
        for i, s in enumerate(phase.scenarios, 1):
            type_label = {
                "baseline": "基线",
                "alternative": "替代",
                "wildcard": "黑天鹅",
            }.get(s.scenarioType, s.scenarioType)
            lines.append(f"**情景 {i}：{s.title}**（{type_label}，概率 {s.probability:.0%}）")
            lines.append("")
            if s.description:
                lines.append(s.description)
                lines.append("")
            if s.keyAssumptions:
                lines.append("关键假设：")
                for a in s.keyAssumptions:
                    lines.append(f"- {a}")
                lines.append("")
            if s.earlySignals:
                lines.append("早期信号：")
                for sig in s.earlySignals:
                    lines.append(f"- {sig}")
                lines.append("")
            lines.append("")

    if phase.signalsToWatch:
        lines.append("### 观测信号")
        lines.append("")
        for signal in sorted(phase.signalsToWatch, key=lambda s: -s.priority):
            priority_bar = "★" * signal.priority + "☆" * (5 - signal.priority)
            lines.append(f"- **{signal.signalName}**  [{priority_bar}]")
            if signal.description:
                lines.append(f"  {signal.description}")
            if signal.indicator:
                lines.append(f"  指标：{signal.indicator}")
            if signal.currentValue:
                lines.append(f"  当前值：{signal.currentValue}")
            if signal.threshold:
                lines.append(f"  阈值：{signal.threshold}")
            if signal.trend:
                lines.append(f"  趋势：{signal.trend}")
            lines.append("")
        lines.append("")

    if phase.lastWeekCalibration:
        lines.append("### 上周校准")
        lines.append("")
        lw = phase.lastWeekCalibration
        if lw.predictionSummary:
            lines.append(f"上周预测：{lw.predictionSummary}")
            lines.append("")
        if lw.actualOutcome:
            lines.append(f"实际结果：{lw.actualOutcome}")
            lines.append("")
        if lw.calibrationNote:
            lines.append(f"校准说明：{lw.calibrationNote}")
            lines.append("")
        if lw.accuracyScore is not None:
            lines.append(f"准确度评分：{lw.accuracyScore:.2f}")
            lines.append("")

    return "\n".join(lines)


# =============================================================================
# Main article generator
# =============================================================================


def generate_article(issue: WeeklyIssue, blog_dir: Path) -> str:
    """Generate a Markdown article from a WeeklyIssue following the five-phase
    dialectical narrative structure.

    Sections (each optional — skipped if the corresponding phase is None):
      一、现象 — Phenomenon Grasping
      二、矛盾 — Contradiction Identification
      三、展开 — Dialectical Unfolding
      四、定位 — Historical Positioning
      五、方向 — Practice Orientation

    Args:
        issue: A fully-analyzed WeeklyIssue with at least phase1 populated.
        blog_dir: Blog output directory (reserved for future use).

    Returns:
        Complete Markdown article string.
    """
    lines: list[str] = _header_lines(issue)

    # ---- five-phase sections ----
    lines.append(_render_phase1(issue.phase1))
    lines.append("")

    if issue.phase2 is not None:
        lines.append(_render_phase2(issue.phase2))
        lines.append("")

    if issue.phase3 is not None:
        lines.append(_render_phase3(issue.phase3))
        lines.append("")

    if issue.phase4 is not None:
        lines.append(_render_phase4(issue.phase4))
        lines.append("")

    if issue.phase5 is not None:
        lines.append(_render_phase5(issue.phase5))
        lines.append("")

    lines.extend(_footer_lines(issue))

    return "\n".join(lines)


def _header_lines(issue: WeeklyIssue) -> list[str]:
    """Build the YAML frontmatter and page header shared by all renderers."""
    events = issue.events
    date_range = _format_date_range(issue.weekStart, issue.weekEnd)
    tagline = _tagline(events)

    keywords: list[str] = ["热点", "周刊", "分析"]
    for e in events:
        for w in e.title[:20].replace("，", " ").replace("、", " ").split():
            if len(w) >= 2 and w not in keywords:
                keywords.append(w)
    if issue.phase2 is not None:
        for s in issue.phase2.interestStructures[:2]:
            if s.interestGroup and s.interestGroup not in keywords:
                keywords.insert(3, s.interestGroup)
    if issue.phase4 is not None:
        for t in issue.phase4.epochThemes[:2]:
            if t.themeName and t.themeName not in keywords:
                keywords.insert(3, t.themeName)

    model_backed = bool(issue.metadata.modelVersions)
    desc = (
        issue.phase1.phaseSummary[:120].replace("\n", " ")
        if issue.phase1.phaseSummary
        else ""
    )
    if not desc:
        sample_titles = "、".join(e.title[:15] for e in events[:3])
        if model_backed:
            desc = (
                f"本周（{issue.weekStart} 至 {issue.weekEnd}）热点事件分析，"
                f"涵盖 {sample_titles}等 {len(events)} 个事件。"
            )
        else:
            desc = (
                f"本周（{issue.weekStart} 至 {issue.weekEnd}）公开热点素材整理，"
                f"涵盖 {sample_titles}等 {len(events)} 个事件。"
            )
    if len(desc) > 150:
        desc = desc[:147] + "..."

    return [
        "---",
        f"title: 每周热点分析 {issue.id}",
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


def _footer_lines(issue: WeeklyIssue) -> list[str]:
    """Evidence summary and attribution footer."""
    lines: list[str] = []
    et = issue.evidenceTrace
    if et.claims:
        lines.append("---")
        lines.append("")
        lines.append(f"*本文共包含 {et.totalVerifiedClaims} 条已验证主张，"
                     f"涉及 {len(et.claims)} 条因果链。*")
        lines.append("")

    lines.extend(_provenance_lines(issue))

    if issue.metadata.modelVersions:
        lines.append(
            "*本文由 [格物 (Dianalyze)](https://github.com/dreamnight16/weekly-hotspot) "
            "根据公开热点素材生成，分析结论和来源仍需读者核对。*"
        )
    else:
        lines.append(
            "*本文由 [格物 (Dianalyze)](https://github.com/dreamnight16/weekly-hotspot) "
            "整理公开热点素材；本期未进行模型分析，请打开来源核对原文。*"
        )
    return lines


def _provenance_lines(issue: WeeklyIssue) -> list[str]:
    """Disclose the analysis status and the evidence cutoff to the reader.

    A system that revises its own judgments has to show its work: readers
    should be able to see when the analysis was made, how far the evidence
    reached, and whether the result was downgraded.
    """
    meta = issue.metadata
    lines: list[str] = []
    facts: list[str] = []
    if meta.analysisDate:
        facts.append(f"分析日期 {meta.analysisDate}")
    if meta.evidenceCutoff:
        facts.append(f"证据截止 {meta.evidenceCutoff}")
    if meta.promptVersion:
        facts.append(f"提示词版本 {meta.promptVersion}")
    if facts:
        lines.append("")
        lines.append(f"*{'　|　'.join(facts)}*")

    gate = issue.publicationGate
    if gate is not None and gate.decision == "DEGRADE":
        lines.append("")
        lines.append(
            "> **本期为降级发布。** 关键事实的证据尚不充分，以下内容以事实摘要、"
            "争议与待核实问题为主，不构成确定性结论。"
        )
    if gate is not None and gate.decision == "BLOCK":
        lines.append("")
        lines.append(
            "> **本期存在未解决的证据问题，已停止发布分析结论。**"
        )
    return lines


def assemble_article(issue: WeeklyIssue, body: str) -> str:
    """Wrap a narrative body with the shared frontmatter and footer."""
    lines = _header_lines(issue)
    lines.append(body.strip())
    lines.append("")
    lines.extend(_footer_lines(issue))
    return "\n".join(lines)


# =============================================================================
# LLM narrative generation, constrained to validated claims
# =============================================================================
# The article is written from a claim ledger rather than polished from the
# analysis output.  Every assertion the writer may use is listed with its type
# and verification status, so "do not overstate" becomes a concrete constraint
# against an enumerated set instead of a general instruction to be careful.

_LEDGER_LABEL = {
    "KEEP": "可写（证据支持）",
    "QUALIFY": "可写但须降低确定性",
    "REWRITE": "须按改写后的表述写",
    "REMOVE": "不可写（无必要证据支持）",
    "RESEARCH": "作为待核实问题写",
    "UNREVIEWED": "未审查，按类型谨慎处理",
}

_TYPE_LABEL = {
    "FACT": "事实",
    "ATTRIBUTED": "归属陈述（某方称）",
    "INFERENCE": "推断",
    "HYPOTHESIS": "假说",
    "VALUE_JUDGMENT": "价值判断",
    "UNKNOWN": "未确定问题",
}


def build_claim_ledger(claims_by_event: dict) -> str:
    """Render the enumerated assertions the writer may draw on."""
    if not claims_by_event:
        return "（无断言清单——本期不得作出任何分析性断言，只写可核实的事实与待查问题。）"

    lines: list[str] = []
    for event_id, claims in claims_by_event.items():
        lines.append(f"### 事件 {event_id}")
        if not claims:
            lines.append("- （该事件未抽取到断言，只能陈述标题与来源）")
            continue
        for c in claims:
            decision = getattr(c, "publicationDecision", "UNREVIEWED")
            label = _LEDGER_LABEL.get(decision, decision)
            type_label = _TYPE_LABEL.get(getattr(c, "type", ""), getattr(c, "type", ""))
            lines.append(
                f"- [{getattr(c, 'claimId', '')}] {type_label}"
                f" / 验证={getattr(c, 'verificationStatus', '')}"
                f" / 处置={label}"
            )
            lines.append(f"  {getattr(c, 'statement', '')}")
    return "\n".join(lines)


def gate_note(gate) -> str:
    """Instruction block reflecting the publication gate decision."""
    if gate is None:
        return ""
    if getattr(gate, "decision", "") == "DEGRADE":
        return (
            "## 发布级别：降级发布\n\n"
            "本期关键事实的证据尚不充分。**只写事实摘要、来源分歧和待核实的问题，"
            "不要给出确定性的分析结论。**结尾应当明确说明还需要什么证据。"
        )
    if getattr(gate, "decision", "") == "BLOCK":
        return (
            "## 发布级别：仅事实通报\n\n"
            "本期存在未解决的证据问题。**只陈述可核实的事实与各方声明，"
            "不得作出任何分析性结论。**"
        )
    return "## 发布级别：正常发布"


def build_article_context(
    issue: WeeklyIssue,
    claims_by_event: Optional[dict] = None,
    dossiers: Optional[list] = None,
    gate=None,
    story_notes: Optional[list] = None,
) -> str:
    """Assemble the writer's input: events, sources, analyses and ledger."""
    from evidence.collector import dossier_claim_context

    parts: list[str] = []

    parts.append("## 本期事件")
    for e in issue.events:
        parts.append(f"### {e.title}")
        if e.eventStatus:
            parts.append(f"事件状态：{e.eventStatus}")
        if e.summary:
            parts.append(e.summary)
        if e.materialContent:
            parts.append(f"物质内容：{e.materialContent}")
        if e.sourceUrl:
            parts.append(f"来源：{e.sourceUrl}")
        parts.append("")

    if dossiers:
        parts.append("## 已获取的来源材料")
        for dossier in dossiers:
            parts.append(f"### {getattr(dossier, 'title', '')}")
            parts.append(dossier_claim_context(dossier))
            conflicts = getattr(dossier, "conflicts", None)
            if conflicts:
                parts.append("来源间分歧：")
                parts.extend(f"- {c}" for c in conflicts)
            parts.append("")

    parts.append("## 分析结果（已按验证结论修订）")
    if issue.phase2 is not None and issue.phase2.overallContradictionLandscape:
        parts.append(issue.phase2.overallContradictionLandscape)
    if issue.phase2 is not None and issue.phase2.commonInterests:
        parts.append(f"共同利益：{'；'.join(issue.phase2.commonInterests)}")
    if issue.phase2 is not None and issue.phase2.potentialContradictions:
        parts.append(f"潜在矛盾：{'；'.join(issue.phase2.potentialContradictions)}")
    if issue.phase4 is not None and issue.phase4.crossCuttingSynthesis:
        parts.append(issue.phase4.crossCuttingSynthesis)
    if issue.phase5 is not None and issue.phase5.overallJudgment:
        parts.append(issue.phase5.overallJudgment)

    if issue.revisionLog:
        parts.append("")
        parts.append("## 本期已修订的判断")
        for rec in issue.revisionLog:
            if getattr(rec, "action", "") in ("KEEP", "UNREVIEWED"):
                continue
            parts.append(
                f"- {getattr(rec, 'path', '')}：{getattr(rec, 'action', '')}"
                f"（{getattr(rec, 'reason', '')}）"
            )

    if story_notes:
        parts.append("")
        parts.append("## 事件追踪：本周相对此前的判断变化")
        parts.append(
            "以下事件此前已被追踪，本周材料出现了变化。"
            "如果本期判断与上期不同，**必须说明为什么改变**，不要静默覆盖。"
        )
        parts.extend(f"- {note}" for note in story_notes)

    parts.append("")
    parts.append("## 断言清单")
    parts.append("你只能写以下清单允许的范围。清单之外的任何分析性断言都不得出现。")
    parts.append("")
    parts.append(build_claim_ledger(claims_by_event or {}))

    return "\n".join(parts)


def generate_narrative_article(
    client,
    issue: WeeklyIssue,
    context: str,
    *,
    gate=None,
    max_tokens: int = 8192,
) -> Optional[str]:
    """Write the article body with the LLM, or return None on any failure.

    Returning None sends the caller back to the deterministic template, which
    is a weaker article but never an unchecked one.
    """
    from prompts import load_prompt

    try:
        prompt = load_prompt("narrative/article").format(
            event_count=len(issue.events),
            dialectical_output=context,
            gate_note=gate_note(gate),
        )
    except (KeyError, IndexError) as exc:
        _log().warning("article prompt 渲染失败: %s", exc)
        return None

    try:
        body = client.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个唯物辩证法取向的新闻写作者。你只能写出输入断言清单"
                        "所允许的内容；清单没有支持的断言一律不得出现。"
                        "严格区分事实、归属陈述、推断与假说，不要把假说写成事实。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
        )
    except Exception as exc:
        _log().warning("narrative 生成失败，回退模板: %s", exc)
        return None

    body = (body or "").strip()
    if not body:
        return None
    # The model is told not to emit frontmatter; strip it defensively so a
    # stray block cannot collide with the one we generate.
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) == 3:
            body = parts[2].strip()
    return body


def _log():
    from config import get_logger

    return get_logger("narrative.article")

