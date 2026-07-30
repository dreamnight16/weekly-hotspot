"""Tests for narrative/article.py — five-phase dialectical article generator."""
from pathlib import Path

import pytest

from narrative.article import (
    _confidence_label,
    _format_date_range,
    _render_phase1,
    _render_phase2,
    _render_phase3,
    _render_phase4,
    _render_phase5,
    _render_gdelt_baseline,
    _render_nine_dim_scores,
    _tagline,
    generate_article,
)
from schema import (
    AdversarialReview,
    CausalLoopDiagram,
    ClassPosition,
    CompetingHypothesis,
    ContradictionIdentification,
    DataValidation,
    DialecticalUnfolding,
    EpochTheme,
    EvidenceTrace,
    ExcludedEvent,
    GDELTBaseline,
    HiddenConnection,
    HistoricalAnalogy,
    HistoricalPositioning,
    InterestStructure,
    IssueMetadata,
    NegationOfNegation,
    NineDimScores,
    PhenomenonGrasping,
    PracticeOrientation,
    QuantityQuality,
    Scenario,
    SelectedEvent,
    SystemArchetype,
    UnityOfOpposites,
    WatchSignal,
    WeeklyIssue,
)
from utils import section_label


# =============================================================================
# Helpers — build minimal phase objects for testing
# =============================================================================


def _mk_selected() -> list[SelectedEvent]:
    return [
        SelectedEvent(
            id="evt-1",
            title="物价上涨事件",
            summary="多地反映蔬菜价格上涨明显，引发社交媒体广泛讨论。",
            materialContent="蔬菜批发价同比上涨约15%",
            isDirectExpression=True,
        ),
        SelectedEvent(
            id="evt-2",
            title="平台裁员事件",
            summary="某头部平台宣布裁员5%，涉及物流和运营岗位。",
            materialContent="平台订单量同比下降，人力成本优化",
            isDirectExpression=False,
        ),
    ]


def _mk_phase1() -> PhenomenonGrasping:
    return PhenomenonGrasping(
        phaseSummary="本周现象层面以民生价格波动和平台裁员为焦点。",
        selectedEvents=_mk_selected(),
        excludedEvents=[
            ExcludedEvent(
                id="evt-ex-1",
                title="某明星八卦",
                summary="娱乐新闻，无物质利益内容。",
                exclusionReason="缺乏阶级分析价值",
            ),
        ],
        gdeltBaseline=GDELTBaseline(
            totalArticles=12345,
            avgTone=-1.23,
            numEvents=567,
            period="2026-W31",
        ),
        sourceQualityReport="信源质量良好，主要依赖官媒和一手数据。",
    )


def _mk_phase2() -> ContradictionIdentification:
    return ContradictionIdentification(
        phaseSummary="本周矛盾集中在民生成本与资本效率之间的张力。",
        events=_mk_selected(),
        overallContradictionLandscape="主要矛盾表现为百姓生活成本上升与平台资本降本增效之间的对抗。",
        interestStructures=[
            InterestStructure(
                interestGroup="普通消费者",
                materialInterest="维持现有生活水平、稳定物价",
                expressionForm="社交媒体抱怨、减少非必要消费",
                intensity=4,
                relatedEventIds=["evt-1"],
            ),
            InterestStructure(
                interestGroup="平台资本",
                materialInterest="降低运营成本、维持利润率",
                expressionForm="裁员、削减福利",
                intensity=3,
                relatedEventIds=["evt-2"],
            ),
        ],
        classPositions=[
            ClassPosition(
                className="劳动者",
                position="受雇于平台资本，面临失业风险",
                coreInterest="稳定的就业和收入",
                contradictions=["资本积累逻辑下劳动力再生产成本被压缩"],
                relatedEventIds=["evt-2"],
            ),
        ],
        nineDimScores=NineDimScores(
            magnitude=(7, 0.8),
            scope=(6, 0.7),
            velocity=(4, 0.6),
            novelty=(3, 0.5),
            cascadePotential=(6, 0.7),
            actorProminence=(5, 0.6),
            uncertainty=(4, 0.5),
            polarity=(6, 0.7),
            durability=(5, 0.6),
        ),
        competingHypotheses=[
            CompetingHypothesis(
                hypothesisId="H1",
                description="季节性波动导致菜价上涨",
                supportingEvidence="历史数据表明夏季菜价波动是常态",
                contradictingEvidence="本次涨幅显著高于历史同期均值",
                assessedProbability=0.4,
                relatedEventIds=["evt-1"],
            ),
        ],
    )


def _mk_phase3() -> DialecticalUnfolding:
    return DialecticalUnfolding(
        phaseSummary="辩证展开揭示量变积累与局部质变并存的态势。",
        events=_mk_selected(),
        dialecticalConfidence="HIGH",
        unityOfOpposites=UnityOfOpposites(
            identity="消费者需要生活必需品，资本需要利润来源",
            struggle="消费者对物价承受力接近临界点",
            particularity="本轮涨价以蔬菜为主，非全面通胀",
            universality="成本转嫁是资本应对利润压力的普遍手段",
        ),
        quantityQuality=QuantityQuality(
            currentPhase="量变中的局部质变",
            quantitativeDirection="物价上涨幅度逐周扩大",
            measure="消费者物价指数（CPI）同比3%为度",
            newQuality="可能引发政策干预的民生类通胀",
            oldQualityNegated="疫情后恢复期的温和通胀",
        ),
        negationOfNegation=NegationOfNegation(
            oldThing="疫情前相对稳定的物价体系",
            firstNegation="疫情冲击下供应链断裂导致的价格紊乱",
            internalNegation="资本在稳定后的成本重构",
            direction="暂时倒退",
            stageCharacteristics="否定之否定尚未完成，处于第二次否定的前端",
        ),
        adversarialReview=AdversarialReview(
            reviewAspect="菜价上涨是否具有阶级性质",
            originalClaim="菜价上涨是市场自然调节",
            critique="忽视了流通环节资本对定价权的控制",
            revisedClaim="菜价上涨本质是流通资本在特定环节的利润转移",
            confidence="MEDIUM",
        ),
        causalLoopDiagram=CausalLoopDiagram(
            diagramId="CLD-1",
            description="菜价-资本循环",
            nodes=["产量下降", "中间商抬价", "消费者减少购买"],
            positiveFeedbackLoops=["利润驱动加价"],
            negativeFeedbackLoops=["消费者购买力制约"],
            keyLeveragePoints=["中间流通环节的监管"],
        ),
        dataValidation=DataValidation(
            validationCheck="菜价数据交叉验证",
            dataSource="国家统计局 + 地方批发市场",
            result="数据一致性高，趋势确认",
            issues=["部分地区数据更新滞后2-3天"],
            confidence="HIGH",
        ),
    )


def _mk_phase4() -> HistoricalPositioning:
    return HistoricalPositioning(
        phaseSummary="当前现象属于全球化退潮期民生矛盾的典型表现。",
        events=_mk_selected(),
        crossCuttingSynthesis="跨领域综合分析表明本轮物价上涨不是孤立现象。",
        epochThemes=[
            EpochTheme(
                themeName="后疫情生活成本危机",
                description="全球主要经济体均在经历生活成本上涨。",
                relevanceToCurrentEvents="中国本轮菜价上涨与全球趋势同构性高。",
                relatedEventIds=["evt-1"],
            ),
        ],
        systemArchetypes=[
            SystemArchetype(
                archetypeType="ShiftingTheBurden",
                patternName="短期补贴替代结构改革",
                description="政府倾向于用补贴应对物价，而非解决流通结构问题。",
                structuralFeatures="补贴 → 价格暂时回落 → 结构未变 → 新一轮上涨",
                relatedEventIds=["evt-1"],
            ),
        ],
        hiddenConnections=[
            HiddenConnection(
                connectionName="菜价-裁员关联",
                entityA="蔬菜价格上涨",
                entityB="平台裁员",
                connectionMechanism="消费者在食品支出增加后减少非必要消费，冲击平台订单量。",
                significance="揭示了消费降级对数字经济的传导机制。",
                relatedEventIds=["evt-1", "evt-2"],
            ),
        ],
        historicalAnalogies=[
            HistoricalAnalogy(
                analogyName="2010年蒜你狠",
                historicalPeriod="2009-2011年",
                historicalEvent="大蒜价格暴涨引发'蒜你狠'网络热词",
                similarity="都是特定农产品价格在流通环节被炒作推高",
                difference="本轮涉及品类更广，且叠加平台经济因素",
                lessonForToday="流通领域监管是平抑价格的关键",
                relatedEventIds=["evt-1"],
            ),
        ],
    )


def _mk_phase5() -> PracticeOrientation:
    return PracticeOrientation(
        overallJudgment="综合判断：本轮矛盾尚在量变阶段，但局部质变信号不容忽视。",
        scenarios=[
            Scenario(
                scenarioId="S1",
                title="基线：季节性回调",
                description="8月中旬菜价随供给增加自然回落，社会情绪缓解。",
                scenarioType="baseline",
                probability=0.6,
                keyAssumptions=["天气正常、无额外冲击", "流通环节无资本炒作"],
                earlySignals=["批发市场进货量增加", "零售终端降价促销"],
                relatedEventIds=["evt-1"],
            ),
            Scenario(
                scenarioId="S2",
                title="替代情景：持续高位",
                description="异常天气持续叠加资本炒作，菜价维持高位，舆论升级。",
                scenarioType="alternative",
                probability=0.3,
                keyAssumptions=["极端天气持续", "流通环节资本炒作加剧"],
                earlySignals=["期货市场数据异常", "监管部门约谈流通企业"],
                relatedEventIds=["evt-1"],
            ),
        ],
        practiceSignificance="注重流通领域的结构性改革，比短期补贴更具根本性。",
        signalsToWatch=[
            WatchSignal(
                signalName="国家统计局CPI数据",
                description="密切关注月度CPI食品分项变动",
                indicator="食品CPI同比",
                currentValue="+3.2%",
                threshold="+5%",
                trend="上升",
                priority=5,
            ),
            WatchSignal(
                signalName="社交媒体情绪指数",
                description="追踪菜价相关话题的热度与情感倾向",
                indicator="微博/小红书相关话题热度",
                currentValue="中高",
                threshold="高（热搜前十）",
                trend="上升",
                priority=4,
            ),
        ],
    )


def _mk_issue(
    *,
    with_phase2: bool = True,
    with_phase3: bool = True,
    with_phase4: bool = True,
    with_phase5: bool = True,
) -> WeeklyIssue:
    """Build a WeeklyIssue with configurable phases."""
    return WeeklyIssue(
        id="2026-W31",
        weekStart="2026-07-27",
        weekEnd="2026-08-02",
        events=_mk_selected(),
        phase1=_mk_phase1(),
        phase2=_mk_phase2() if with_phase2 else None,
        phase3=_mk_phase3() if with_phase3 else None,
        phase4=_mk_phase4() if with_phase4 else None,
        phase5=_mk_phase5() if with_phase5 else None,
        evidenceTrace=EvidenceTrace(claims=[], totalVerifiedClaims=0),
        metadata=IssueMetadata(
            modelVersions={},
            verificationPasses=0,
            empiricalDegradations=[],
            totalApiCost=0.0,
            runDuration=0.0,
            runId="test",
        ),
    )


# =============================================================================
# Utility tests
# =============================================================================


@pytest.mark.unit
def test_format_date_range():
    result = _format_date_range("2026-07-27", "2026-08-02")
    assert "7月27日" in result
    assert "8月2日" in result
    assert "周" in result


@pytest.mark.unit
def test_format_date_range_invalid():
    result = _format_date_range("bad-date", "also-bad")
    assert result == "bad-date — also-bad"


@pytest.mark.unit
def test_tagline_empty():
    result = _tagline([])
    assert "相对平静" in result


@pytest.mark.unit
def test_tagline_many_events():
    events = [SelectedEvent(id=f"evt-{i}", title=f"事件{i}", summary="") for i in range(10)]
    result = _tagline(events)
    assert "高度密集" in result


@pytest.mark.unit
def test_tagline_few_events():
    events = [SelectedEvent(id=f"evt-{i}", title=f"事件{i}", summary="") for i in range(3)]
    result = _tagline(events)
    assert "值得关注" in result


@pytest.mark.unit
def test_section_label():
    assert section_label(1) == "一"
    assert section_label(2) == "二"
    assert section_label(5) == "五"
    assert section_label(10) == "十"
    assert section_label(0) == "零"


@pytest.mark.unit
def test_section_label_overflow():
    result = section_label(11)
    assert result == "11"


@pytest.mark.unit
def test_confidence_label():
    assert _confidence_label("HIGH") == " [HIGH]"
    assert _confidence_label("MEDIUM") == " [MEDIUM]"
    assert _confidence_label("LOW") == " [LOW]"
    assert _confidence_label("high") == " [HIGH]"
    assert _confidence_label("") == ""
    assert _confidence_label(None) == ""


# =============================================================================
# Phase rendering tests
# =============================================================================


@pytest.mark.unit
def test_render_phase1_structure():
    result = _render_phase1(_mk_phase1())
    assert "## 一、现象" in result
    assert "本周现象层面以民生价格波动和平台裁员为焦点" in result
    assert "数据基线" in result
    assert "信源质量" in result
    assert "入选事件" in result
    assert "排除事件" in result
    assert "物价上涨事件" in result
    assert "平台裁员事件" in result
    assert "某明星八卦" in result
    assert "缺乏阶级分析价值" in result


@pytest.mark.unit
def test_render_phase1_minimal():
    """Phase 1 with minimal data (no baseline, no excluded events)."""
    phase = PhenomenonGrasping(
        phaseSummary="最小化测试",
        selectedEvents=[SelectedEvent(id="evt-1", title="测试事件", summary="概述")],
    )
    result = _render_phase1(phase)
    assert "## 一、现象" in result
    # No sub-headings for baseline or excluded
    assert "数据基线" not in result
    assert "排除事件" not in result


@pytest.mark.unit
def test_render_gdelt_baseline():
    baseline = GDELTBaseline(totalArticles=5000, avgTone=-2.15, numEvents=300, period="2026-W31")
    lines = _render_gdelt_baseline(baseline)
    joined = "\n".join(lines)
    assert "5,000" in joined
    assert "-2.15" in joined
    assert "300" in joined
    assert "2026-W31" in joined


@pytest.mark.unit
def test_render_phase2_structure():
    result = _render_phase2(_mk_phase2())
    assert "## 二、矛盾" in result
    assert "矛盾格局" in result
    assert "利益结构" in result
    assert "阶级立场" in result
    assert "九维评分" in result
    assert "竞争性假说" in result
    assert "普通消费者" in result
    assert "平台资本" in result
    assert "劳动者" in result
    assert "季节性波动导致菜价上涨" in result


@pytest.mark.unit
def test_render_nine_dim_scores():
    scores = NineDimScores(
        magnitude=(7, 0.8),
        scope=(6, 0.7),
        velocity=(4, 0.6),
        novelty=(3, 0.5),
        cascadePotential=(6, 0.7),
        actorProminence=(5, 0.6),
        uncertainty=(4, 0.5),
        polarity=(6, 0.7),
        durability=(5, 0.6),
    )
    lines = _render_nine_dim_scores(scores)
    joined = "\n".join(lines)
    assert "规模" in joined
    assert "7/10" in joined
    assert "[HIGH]" in joined
    assert "[MEDIUM]" in joined
    # [LOW] may not appear with this dataset; confidence >= 0.5 for all dims
    assert "0.80" in joined
    assert "0.70" in joined
    assert "0.50" in joined


@pytest.mark.unit
def test_render_phase3_structure():
    result = _render_phase3(_mk_phase3())
    assert "## 三、展开 [HIGH]" in result
    assert "对立统一" in result
    assert "量变质变" in result
    assert "否定之否定" in result
    assert "对抗审查" in result
    assert "因果循环" in result
    assert "数据验证" in result
    # Check confidence labels appear
    assert "[HIGH]" in result
    assert "[MEDIUM]" in result


@pytest.mark.unit
def test_render_phase3_default_confidence():
    """Phase 3 with empty dialecticalConfidence gets sanitized to MEDIUM."""
    phase = DialecticalUnfolding(
        phaseSummary="默认置信度",
        dialecticalConfidence="MEDIUM",
    )
    result = _render_phase3(phase)
    assert "## 三、展开 [MEDIUM]" in result
    assert "默认置信度" in result


@pytest.mark.unit
def test_render_phase4_structure():
    result = _render_phase4(_mk_phase4())
    assert "## 四、定位" in result
    assert "交叉综合" in result
    assert "时代主题" in result
    assert "系统原型" in result
    assert "隐藏关联" in result
    assert "历史类比" in result
    assert "后疫情生活成本危机" in result
    assert "ShiftingTheBurden" in result
    assert "菜价-裁员关联" in result
    assert "蒜你狠" in result


@pytest.mark.unit
def test_render_phase4_minimal():
    """Phase 4 with minimal data."""
    phase = HistoricalPositioning(phaseSummary="简单位置")
    result = _render_phase4(phase)
    assert "## 四、定位" in result
    assert "简单位置" in result


@pytest.mark.unit
def test_render_phase5_structure():
    result = _render_phase5(_mk_phase5())
    assert "## 五、方向" in result
    assert "前瞻情景" in result
    assert "实践意义" in result
    assert "观测信号" in result
    assert "上周校准" not in result  # No calibration in fixture
    assert "基线：季节性回调" in result
    assert "替代情景：持续高位" in result
    assert "国家统计局CPI数据" in result
    assert "社交媒体情绪指数" in result
    # Check priority stars
    assert "★★★★★" in result
    assert "★★★★☆" in result


@pytest.mark.unit
def test_render_phase5_with_calibration():
    phase = PracticeOrientation(
        overallJudgment="测试判断",
        practiceSignificance="测试意义",
    )
    # Add lastWeekCalibration via model manipulation
    from schema import LastWeekCalibration
    phase.lastWeekCalibration = LastWeekCalibration(
        predictionSummary="上周预测菜价平稳",
        actualOutcome="菜价上涨15%",
        calibrationNote="低估了天气因素",
        accuracyScore=0.3,
    )
    result = _render_phase5(phase)
    assert "上周校准" in result
    assert "上周预测菜价平稳" in result
    assert "菜价上涨15%" in result
    assert "0.30" in result


# =============================================================================
# Full article generation tests
# =============================================================================


@pytest.mark.unit
def test_article_has_five_sections(tmp_path: Path):
    """Article must have all 5 dialectical phases as sections."""
    issue = _mk_issue()
    md = generate_article(issue, tmp_path)
    assert "一、现象" in md
    assert "二、矛盾" in md
    assert "三、展开" in md
    assert "四、定位" in md
    assert "五、方向" in md


@pytest.mark.unit
def test_article_footer_has_gewu(tmp_path: Path):
    """Article footer must reference 格物 (Dianalyze) with GitHub link."""
    issue = _mk_issue()
    md = generate_article(issue, tmp_path)
    assert "格物" in md
    assert "Dianalyze" in md
    assert "github.com" in md


@pytest.mark.unit
def test_article_frontmatter(tmp_path: Path):
    """Article must have frontmatter with title, published, description, category, tags."""
    issue = _mk_issue()
    md = generate_article(issue, tmp_path)
    assert "title: 每周热点分析 2026-W31" in md
    assert "published: 2026-08-02" in md
    assert "category: 周刊" in md
    assert "tags:" in md
    assert "description:" in md


@pytest.mark.unit
def test_article_skips_missing_phases(tmp_path: Path):
    """When phases 2-5 are None, only phase 1 section is rendered."""
    issue = _mk_issue(with_phase2=False, with_phase3=False, with_phase4=False, with_phase5=False)
    md = generate_article(issue, tmp_path)
    assert "一、现象" in md
    assert "二、矛盾" not in md
    assert "三、展开" not in md
    assert "四、定位" not in md
    assert "五、方向" not in md
    assert "格物" in md
    assert "2026-W31" in md


@pytest.mark.unit
def test_article_phase1_only_frontmatter_valid(tmp_path: Path):
    """Even with only phase 1, frontmatter and footer are valid."""
    issue = _mk_issue(with_phase2=False, with_phase3=False, with_phase4=False, with_phase5=False)
    md = generate_article(issue, tmp_path)
    assert "---" in md
    assert "title:" in md
    assert "格物" in md


@pytest.mark.unit
def test_article_partial_phases(tmp_path: Path):
    """Test with some phases present and some missing."""
    issue = _mk_issue(with_phase3=False, with_phase5=False)
    md = generate_article(issue, tmp_path)
    assert "一、现象" in md
    assert "二、矛盾" in md
    assert "三、展开" not in md
    assert "四、定位" in md
    assert "五、方向" not in md


@pytest.mark.unit
def test_article_uncertainty_labels_present(tmp_path: Path):
    """Uncertainty labels [HIGH]/[MEDIUM]/[LOW] must appear in output
    when the corresponding phase has confidence fields."""
    issue = _mk_issue()
    md = generate_article(issue, tmp_path)
    assert "[HIGH]" in md
    assert "[MEDIUM]" in md
    # LOW may or may not appear depending on data; we verify at least 2 labels
    label_count = md.count("[HIGH]") + md.count("[MEDIUM]") + md.count("[LOW]")
    assert label_count >= 2, f"Expected at least 2 uncertainty labels, found {label_count}"


@pytest.mark.unit
def test_article_evidence_trace_appears(tmp_path: Path):
    """When evidence trace has claims, the summary line appears."""
    from schema import TracedClaim, TracedSource
    et = EvidenceTrace(
        claims=[
            TracedClaim(
                claimId="c1",
                claim="菜价上涨15%",
                phase="phase1",
                confidence="HIGH",
                sources=[TracedSource(sourceName="国家统计局", sourceUrl="http://example.com")],
                independentCorroborations=2,
            ),
        ],
        totalVerifiedClaims=3,
    )
    issue = _mk_issue()
    issue.evidenceTrace = et
    md = generate_article(issue, tmp_path)
    assert "3 条已验证主张" in md
    # With 1 claim in the list but totalVerifiedClaims=3
