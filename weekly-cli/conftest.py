"""Shared pytest fixtures and marker registration for weekly-cli tests."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests that run without network/API calls")
    config.addinivalue_line("markers", "integration: Integration tests that require DEEPSEEK_API_KEY")
    # Ensure unit tests don't trigger config.py's sys.exit(1) when API key is unset
    if "DEEPSEEK_API_KEY" not in os.environ:
        os.environ["DEEPSEEK_API_KEY"] = "sk-pytest-dummy-key"


SAMPLE_EVENT_DICT = {
    "id": "evt-1",
    "title": "测试事件",
    "impactScore": 4,
    "infoGainScore": 3,
    "summary": "这是一个测试事件的概述。",
    "classAnalysis": {
        "classNature": "资本扩张",
        "contradiction": "劳资矛盾",
        "historicalContext": "全球化退潮期",
    },
    "dialecticalSummary": "该事件体现了资本在追求利润过程中与劳动者的矛盾激化。",
    "timeline": [
        {
            "id": "tl-1-1",
            "time": "2026-05-18T10:00:00+08:00",
            "title": "首次报道",
            "description": "媒体首次报道此事。",
            "evidenceRefs": ["ev-1-1"],
        }
    ],
    "evidence": [
        {
            "id": "ev-1-1",
            "sourceType": "官媒",
            "sourceName": "人民日报",
            "sourceUrl": "https://example.com/news/1",
            "content": "相关报道内容摘要。",
            "authenticity": "真实",
            "aiReason": "来源权威，多方交叉验证一致。",
            "classBias": "无产阶级立场",
        }
    ],
    "edges": [
        {
            "from": "tl-1-1",
            "to": "ev-1-1",
            "type": "关联",
            "description": "该报道为时间线节点的信息来源。",
        }
    ],
}


@pytest.fixture
def sample_event() -> dict:
    return json.loads(json.dumps(SAMPLE_EVENT_DICT))


@pytest.fixture
def sample_events() -> list[dict]:
    return [
        {
            "id": "evt-1",
            "title": "事件一",
            "impactScore": 5,
            "infoGainScore": 4,
            "summary": "事件一概述",
            "classAnalysis": {
                "classNature": "资本扩张",
                "contradiction": "劳资矛盾",
                "historicalContext": "数字经济发展期",
            },
            "dialecticalSummary": "事件一辩证总结",
            "timeline": [
                {"id": "tl-1-1", "time": "2026-01-01T00:00:00", "title": "节点1", "description": "描述1", "evidenceRefs": ["ev-1-1"]},
                {"id": "tl-1-2", "time": "2026-01-02T00:00:00", "title": "节点2", "description": "描述2", "evidenceRefs": ["ev-1-2"]},
                {"id": "tl-1-3", "time": "2026-01-03T00:00:00", "title": "节点3", "description": "描述3", "evidenceRefs": ["ev-1-3"]},
            ],
            "evidence": [
                {"id": "ev-1-1", "sourceType": "官媒", "sourceName": "新华社", "content": "证据1", "authenticity": "真实", "aiReason": "官方发布", "classBias": "待判断"},
                {"id": "ev-1-2", "sourceType": "社交平台", "sourceName": "微博", "content": "证据2", "authenticity": "存疑", "aiReason": "待核实", "classBias": "待判断"},
                {"id": "ev-1-3", "sourceType": "一手材料", "sourceName": "现场", "content": "证据3", "authenticity": "真实", "aiReason": "一手", "classBias": "待判断"},
            ],
            "edges": [
                {"from": "tl-1-1", "to": "tl-1-2", "type": "因果", "description": "关联"},
            ],
        },
        {
            "id": "evt-2",
            "title": "事件二",
            "impactScore": 3,
            "infoGainScore": 3,
            "summary": "事件二概述",
            "classAnalysis": {
                "classNature": "金融资本流动",
                "contradiction": "跨国资本与本土政策",
                "historicalContext": "全球加息周期",
            },
            "dialecticalSummary": "事件二辩证总结",
            "timeline": [
                {"id": "tl-2-1", "time": "2026-01-04T00:00:00", "title": "节点A", "description": "描述A", "evidenceRefs": ["ev-2-1"]},
                {"id": "tl-2-2", "time": "2026-01-05T00:00:00", "title": "节点B", "description": "描述B", "evidenceRefs": ["ev-2-2"]},
                {"id": "tl-2-3", "time": "2026-01-06T00:00:00", "title": "节点C", "description": "描述C", "evidenceRefs": ["ev-2-3"]},
            ],
            "evidence": [
                {"id": "ev-2-1", "sourceType": "官媒", "sourceName": "央视", "content": "证据A", "authenticity": "真实", "aiReason": "官方", "classBias": "待判断"},
                {"id": "ev-2-2", "sourceType": "其他", "sourceName": "分析", "content": "证据B", "authenticity": "待验证", "aiReason": "待核实", "classBias": "待判断"},
                {"id": "ev-2-3", "sourceType": "社交平台", "sourceName": "知乎", "content": "证据C", "authenticity": "存疑", "aiReason": "个人观点", "classBias": "小资产阶级立场"},
            ],
            "edges": [
                {"from": "tl-2-1", "to": "tl-2-2", "type": "关联", "description": "关联"},
            ],
        },
    ]


@pytest.fixture
def sample_synthesis() -> dict:
    return {
        "weeklyNarrative": "本周多个事件从不同侧面反映了资本在科技、劳动、金融三个领域的集中化趋势。",
        "crossCuttingThemes": [
            {
                "name": "平台资本对劳动者的成本转嫁",
                "description": "多个事件显示平台企业通过调整抽成、定价等机制将运营成本转嫁给劳动者",
                "relatedEventIds": ["evt-1", "evt-2"],
                "significance": "揭示了数字资本主义下'灵活用工'模式的结构性矛盾",
            }
        ],
        "trends": [
            {
                "name": "政府监管力度加大",
                "description": "本周多个事件显示监管部门对科技公司的介入在增加",
                "direction": "上升",
                "evidenceEventIds": ["evt-1"],
            }
        ],
        "contradictionsInMotion": [
            {
                "contradiction": "资本积累与劳动者权益保护之间的矛盾",
                "opposingForces": "平台资本追求利润最大化的动力 与 劳动者通过政策和集体行动争取权益",
                "eventsInvolved": ["evt-1", "evt-2"],
                "currentState": "对抗激化",
                "outlook": "短期内矛盾将继续激化，但政策介入可能在一定程度上缓解极端对抗",
            }
        ],
        "globalAssessment": "本周核心矛盾运动处于积累期，多个领域的量变在向质变逼近。",
        "dataGaps": ["缺乏事件二中企业内部决策的具体信息"],
    }


@pytest.fixture
def tmp_cache_dir():
    """Redirect cache.CACHE_DIR to a temporary directory."""
    from scraper import cache
    with tempfile.TemporaryDirectory() as td:
        original = cache.CACHE_DIR
        cache.CACHE_DIR = Path(td)
        cache.CACHE_FILE = Path(td) / "last_raw_events.json"
        yield
        cache.CACHE_DIR = original
        cache.CACHE_FILE = original / "last_raw_events.json"


# =============================================================================
# v2 Pipeline Fixtures
# =============================================================================


@pytest.fixture
def sample_grasping() -> dict:
    """Phase 1: PhenomenonGrasping output for pipeline testing."""
    return {
        "phaseSummary": "本周共收集12个热点事件，经初步筛选留下3个有物质利益分析价值的事件。",
        "selectedEvents": [
            {
                "id": "evt-1",
                "title": "某平台调整骑手抽成比例引发争议",
                "summary": "外卖平台将骑手抽成比例从20%提高至25%，引发骑手集体抗议。",
                "sourceUrl": "https://example.com/news/1",
                "materialContent": "平台资本通过提高抽成比例转嫁成本给劳动者",
                "isDirectExpression": True,
                "sourceGrade": {
                    "reliability": "B",
                    "credibility": 2,
                    "rationale": "多家媒体交叉报道，信息一致",
                },
            },
            {
                "id": "evt-2",
                "title": "某城市发布楼市新政松绑限购",
                "summary": "地方政府发布通知，放宽购房限制，刺激房地产市场。",
                "sourceUrl": "https://example.com/news/2",
                "materialContent": "地方政府通过政策工具调节房地产供需关系",
                "isDirectExpression": False,
                "sourceGrade": {
                    "reliability": "A",
                    "credibility": 1,
                    "rationale": "官方文件发布，来源确定",
                },
            },
            {
                "id": "evt-3",
                "title": "AI大模型公司完成新一轮融资",
                "summary": "某AI公司宣布完成10亿美元融资，估值达百亿美元。",
                "sourceUrl": "https://example.com/news/3",
                "materialContent": "资本向AI领域持续集中，技术生产力与资本所有权的矛盾",
                "isDirectExpression": True,
                "sourceGrade": {
                    "reliability": "B",
                    "credibility": 2,
                    "rationale": "公司公告确认，多家财经媒体引用",
                },
            },
        ],
        "excludedEvents": [
            {
                "id": "ex-1",
                "title": "某明星发布新专辑",
                "summary": "娱乐新闻，无物质利益分析价值。",
                "exclusionReason": "纯娱乐事件，缺乏阶级分析价值",
            },
        ],
        "gdeltBaseline": None,
        "sourceQualityReport": "本周信源质量总体良好，主要依赖官方文件和主流媒体报道。",
    }


@pytest.fixture
def sample_contradiction() -> dict:
    """Phase 2: ContradictionIdentification output for pipeline testing."""
    return {
        "phaseSummary": "本周三个事件从不同侧面反映了资本与劳动、中央与地方、技术与资本三组矛盾。",
        "events": [
            {
                "id": "evt-1",
                "title": "某平台调整骑手抽成比例引发争议",
                "summary": "外卖平台将骑手抽成比例从20%提高至25%",
                "materialContent": "平台资本通过提高抽成比例转嫁成本给劳动者",
                "isDirectExpression": True,
            },
            {
                "id": "evt-2",
                "title": "某城市发布楼市新政松绑限购",
                "summary": "地方政府发布通知，放宽购房限制",
                "materialContent": "地方政府通过政策工具调节房地产供需关系",
                "isDirectExpression": False,
            },
            {
                "id": "evt-3",
                "title": "AI大模型公司完成新一轮融资",
                "summary": "某AI公司宣布完成10亿美元融资",
                "materialContent": "资本向AI领域持续集中",
                "isDirectExpression": True,
            },
        ],
        "overallContradictionLandscape": "本周矛盾格局呈现多领域共振特征：劳动关系领域对抗激化，房地产领域政策博弈深化，科技领域资本加速集中。",
        "interestStructures": [
            {
                "interestGroup": "平台资本",
                "materialInterest": "通过提高抽成比例维持利润率",
                "expressionForm": "单方面修改合作协议",
                "intensity": 4,
                "relatedEventIds": ["evt-1"],
            },
            {
                "interestGroup": "外卖骑手",
                "materialInterest": "维持或提高实际收入水平",
                "expressionForm": "集体抗议和舆论施压",
                "intensity": 4,
                "relatedEventIds": ["evt-1"],
            },
        ],
        "classPositions": [
            {
                "className": "平台资本所有者",
                "position": "数字平台生产资料的控制者",
                "coreInterest": "最大化资本回报率和市场份额",
                "contradictions": ["与劳动者的分配矛盾", "与传统产业的竞争矛盾"],
                "relatedEventIds": ["evt-1", "evt-3"],
            },
        ],
        "nineDimScores": {
            "magnitude": [7, 0.8],
            "scope": [6, 0.7],
            "velocity": [8, 0.9],
            "novelty": [5, 0.6],
            "cascadePotential": [7, 0.7],
            "actorProminence": [6, 0.8],
            "uncertainty": [5, 0.5],
            "polarity": [8, 0.8],
            "durability": [6, 0.6],
        },
        "competingHypotheses": [
            {
                "hypothesisId": "H1",
                "description": "平台提高抽成是成本压力下的被动选择",
                "supportingEvidence": "行业整体利润率下降",
                "contradictingEvidence": "公司季度财报显示利润同比增长",
                "assessedProbability": 0.4,
                "relatedEventIds": ["evt-1"],
            },
        ],
    }


@pytest.fixture
def sample_unfolding() -> dict:
    """Phase 3: DialecticalUnfolding per-event output for pipeline testing."""
    return {
        "phaseSummary": "该事件体现了数字资本主义下劳资矛盾从量变向局部质变的过渡。",
        "events": [
            {
                "id": "evt-1",
                "title": "某平台调整骑手抽成比例引发争议",
                "summary": "外卖平台将骑手抽成比例从20%提高至25%，引发骑手集体抗议。",
                "materialContent": "平台资本通过提高抽成比例转嫁成本给劳动者",
                "isDirectExpression": True,
            },
        ],
        "dialecticalConfidence": "HIGH",
        "unityOfOpposites": {
            "identity": "平台与骑手在配送服务价值创造中相互依存",
            "struggle": "双方围绕配送收益的分配比例展开博弈",
            "particularity": "平台经济的算法控制使劳动者缺乏传统劳资谈判渠道",
            "universality": "资本追求剩余价值最大化与劳动者追求报酬合理化的矛盾具有普遍性",
        },
        "quantityQuality": {
            "currentPhase": "量变积累",
            "quantitativeDirection": "抽成比例从20%到25%的变化超过劳动者承受阈值",
            "measure": "劳动者最低生活保障线与平台利润率的平衡点",
            "newQuality": "可能催生新型劳动者组织方式和议价机制",
            "oldQualityNegated": "原有'灵活用工'的劳资关系框架被挑战",
        },
        "negationOfNegation": {
            "oldThing": "传统雇佣关系下的固定工资制",
            "firstNegation": "平台经济下的'灵活用工+算法控制'模式",
            "internalNegation": "骑手集体抗议与舆论压力倒逼平台调整政策",
            "direction": "螺旋上升",
            "stageCharacteristics": "劳动者自组织意识的觉醒与新技术条件下的集体行动形式探索",
        },
        "adversarialReview": {
            "reviewAspect": "关于矛盾对立统一性的认定",
            "originalClaim": "平台与骑手的矛盾是典型的劳资矛盾",
            "critique": "外卖骑手与平台的关系不完全等同于传统雇佣关系，其法律地位为'独立承包商'而非员工",
            "revisedClaim": "矛盾本质是资本与劳动的矛盾，但表现形式为平台经济特有的'类雇佣关系'矛盾",
            "confidence": "MEDIUM",
        },
        "causalLoopDiagram": {
            "diagramId": "cld-001",
            "description": "平台抽成与骑手抗议的因果循环",
            "nodes": ["平台利润需求", "抽成比例", "骑手收入", "骑手抗议", "舆论压力", "政策介入"],
            "positiveFeedbackLoops": ["抽成提高→骑手抗议→舆论扩大→更多骑手加入"],
            "negativeFeedbackLoops": ["政策介入→限制抽成比例→平台利润下降→调整经营策略"],
            "keyLeveragePoints": ["政策介入", "骑手组织化程度"],
        },
        "dataValidation": {
            "validationCheck": "抽成比例的准确性验证",
            "dataSource": "多家媒体交叉报道和平台公告",
            "result": "20%至25%的变化幅度得到多方确认",
            "issues": [],
            "confidence": "HIGH",
        },
    }


@pytest.fixture
def sample_weekly_issue(sample_grasping, sample_contradiction, sample_unfolding) -> dict:
    """Complete WeeklyIssue payload for integration testing."""
    from datetime import datetime
    today = datetime.now()
    iso = today.isocalendar()

    return {
        "id": f"{today.year}-W{iso.week:02d}",
        "weekStart": (today - __import__("datetime").timedelta(days=today.weekday())).strftime("%Y-%m-%d"),
        "weekEnd": (today + __import__("datetime").timedelta(days=6 - today.weekday())).strftime("%Y-%m-%d"),
        "events": sample_unfolding["events"],
        "phase1": sample_grasping,
        "phase2": sample_contradiction,
        "phase3": sample_unfolding,
        "phase4": None,
        "phase5": None,
        "evidenceTrace": {
            "claims": [],
            "totalVerifiedClaims": 0,
        },
        "metadata": {
            "modelVersions": {
                "dialectical": "deepseek-v4-pro",
                "empirical": "deepseek-v4-flash",
            },
            "verificationPasses": 0,
            "empiricalDegradations": [],
            "totalApiCost": 0.0,
            "runDuration": 0.0,
            "runId": "test-run-id",
        },
    }
