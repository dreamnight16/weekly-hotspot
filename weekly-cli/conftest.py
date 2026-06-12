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
    import cache
    with tempfile.TemporaryDirectory() as td:
        original = cache.CACHE_DIR
        cache.CACHE_DIR = Path(td)
        cache.CACHE_FILE = Path(td) / "last_raw_events.json"
        yield
        cache.CACHE_DIR = original
        cache.CACHE_FILE = original / "last_raw_events.json"
