"""Test Empirical Layer: GBN Scenario Planning & Leading Indicators."""
import json
import pytest
from unittest.mock import MagicMock

from empirical.scenarios import (
    plan_scenarios,
    _serialize_synthesis,
    _has_minimal_synthesis_content,
)


class TestSerializeSynthesis:
    def test_serializes_synthesis(self):
        synthesis = {"weeklyNarrative": "本周叙事", "globalAssessment": "总体评估"}
        text = _serialize_synthesis(synthesis)
        assert "本周叙事" in text
        assert isinstance(text, str)

    def test_handles_empty_dict(self):
        text = _serialize_synthesis({})
        assert isinstance(text, str)

    def test_truncates_long_fields(self):
        synthesis = {"weeklyNarrative": "x" * 5000, "globalAssessment": "y"}
        text = _serialize_synthesis(synthesis)
        # The narrative field should be truncated
        assert "(truncated)" in text

    def test_handles_nested_lists(self):
        synthesis = {
            "weeklyNarrative": "叙事",
            "crossCuttingThemes": [{"name": "主题1", "description": "描述1"}],
        }
        text = _serialize_synthesis(synthesis)
        assert "主题1" in text


class TestHasMinimalSynthesisContent:
    def test_returns_true_with_weekly_narrative(self):
        assert _has_minimal_synthesis_content({"weeklyNarrative": "叙事"}) is True

    def test_returns_true_with_cross_cutting_themes(self):
        assert _has_minimal_synthesis_content({
            "crossCuttingThemes": [{"name": "主题1"}],
        }) is True

    def test_returns_false_for_empty_dict(self):
        assert _has_minimal_synthesis_content({}) is False

    def test_returns_false_for_none(self):
        assert _has_minimal_synthesis_content(None) is False

    def test_returns_false_for_empty_themes_list(self):
        assert _has_minimal_synthesis_content({"crossCuttingThemes": []}) is False


class TestPlanScenarios:
    def test_returns_none_on_none_client(self):
        """Graceful degradation when client is None."""
        result = plan_scenarios(None, {"weeklyNarrative": "叙事"})
        assert result is None

    def test_returns_none_on_empty_synthesis(self):
        """Graceful degradation with empty synthesis."""
        mock_client = MagicMock()
        result = plan_scenarios(mock_client, {})
        assert result is None

    def test_returns_none_on_none_synthesis(self):
        """Graceful degradation with None synthesis."""
        mock_client = MagicMock()
        result = plan_scenarios(mock_client, None)
        assert result is None

    def test_returns_none_on_client_error(self):
        """Graceful degradation when LLM call raises."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = RuntimeError("API timeout")
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        assert result is None

    def test_returns_none_on_json_decode_error(self):
        """Graceful degradation on invalid JSON response."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = json.JSONDecodeError("bad", "{", 0)
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        assert result is None

    def test_returns_none_on_non_dict_response(self):
        """Graceful degradation when response is not a dict."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = "not a dict"
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        assert result is None

    def test_calls_chat_json_with_correct_prompt(self):
        """Test LLM call with correct scenarios prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "scenarioSummary": "情景规划总述",
            "predeterminedElements": [
                {
                    "element": "技术持续进步",
                    "description": "AI技术继续快速发展",
                    "evidenceEventIds": ["evt-1"],
                }
            ],
            "keyUncertainties": [
                {
                    "axis": "监管力度",
                    "polarityA": "加强监管",
                    "polarityB": "放松监管",
                    "rationale": "政策方向不明",
                }
            ],
            "scenarios": [
                {
                    "scenarioId": "S1",
                    "title": "稳步发展",
                    "description": "基准发展路径",
                    "scenarioType": "baseline",
                    "probability": 0.45,
                    "keyAssumptions": ["经济平稳", "政策温和"],
                    "earlySignals": ["GDP数据", "政策声明"],
                    "implications": "维持当前策略",
                    "relatedEventIds": ["evt-1"],
                },
                {
                    "scenarioId": "S2",
                    "title": "监管收紧",
                    "description": "替代发展路径",
                    "scenarioType": "alternative",
                    "probability": 0.3,
                    "keyAssumptions": ["政策转向"],
                    "earlySignals": ["监管文件"],
                    "implications": "调整策略",
                    "relatedEventIds": ["evt-2"],
                },
                {
                    "scenarioId": "S3",
                    "title": "黑天鹅事件",
                    "description": "低概率高影响",
                    "scenarioType": "wildcard",
                    "probability": 0.1,
                    "keyAssumptions": ["突发事件"],
                    "earlySignals": ["预警信号"],
                    "implications": "应急准备",
                    "relatedEventIds": ["evt-1", "evt-3"],
                },
            ],
            "leadingIndicators": [
                {
                    "signalName": "政策信号",
                    "description": "监管政策变化",
                    "indicator": "政策文件数量",
                    "currentValue": "正常",
                    "threshold": "超过X个",
                    "trend": "上升",
                    "priority": 4,
                    "relatedScenarioIds": ["S1", "S2"],
                }
            ],
        }
        synthesis = {
            "weeklyNarrative": "本周多个事件反映了资本集中化趋势",
            "crossCuttingThemes": [
                {
                    "name": "平台资本对劳动者的成本转嫁",
                    "description": "多个事件显示平台企业通过调整抽成、定价等机制将运营成本转嫁给劳动者",
                    "relatedEventIds": ["evt-1", "evt-2"],
                    "significance": "结构性矛盾",
                }
            ],
            "trends": [
                {
                    "name": "政府监管力度加大",
                    "description": "监管在增加",
                    "direction": "上升",
                    "evidenceEventIds": ["evt-1"],
                }
            ],
            "contradictionsInMotion": [
                {
                    "contradiction": "资本积累与劳动者权益",
                    "opposingForces": "资本 vs 劳动者",
                    "eventsInvolved": ["evt-1"],
                    "currentState": "激化",
                    "outlook": "短期继续激化",
                }
            ],
            "globalAssessment": "本周核心矛盾运动处于积累期",
            "dataGaps": ["缺乏具体数据"],
        }
        result = plan_scenarios(mock_client, synthesis)

        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]
        user_content = call_args[1]["content"]
        assert "资本集中化趋势" in user_content

        assert result is not None
        assert "scenarioSummary" in result
        assert "predeterminedElements" in result
        assert "keyUncertainties" in result
        assert "scenarios" in result
        assert len(result["scenarios"]) == 3

        # Check scenario types
        types = {s["scenarioType"] for s in result["scenarios"]}
        assert types == {"baseline", "alternative", "wildcard"}

        assert "leadingIndicators" in result
        assert len(result["leadingIndicators"]) == 1

    def test_defaults_applied_to_missing_fields(self):
        """Test defaults when LLM omits fields from response."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "scenarioSummary": "总述",
            # scenarios, leadingIndicators etc. missing
        }
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        assert result is not None
        assert result["scenarios"] == []
        assert result["leadingIndicators"] == []
        assert result["predeterminedElements"] == []
        assert result["keyUncertainties"] == []

    def test_sanitizes_non_list_scenarios(self):
        """Test that non-list scenarios is replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "scenarioSummary": "S",
            "predeterminedElements": [],
            "keyUncertainties": [],
            "scenarios": "not a list",
        }
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        assert result["scenarios"] == []

    def test_sanitizes_scenario_types(self):
        """Test that scenario types are normalized."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "scenarioSummary": "S",
            "predeterminedElements": [],
            "keyUncertainties": [],
            "scenarios": [
                {"scenarioId": "S1", "title": "T1", "description": "D", "scenarioType": "baseline"},
                {"scenarioId": "S2", "title": "T2", "description": "D", "scenarioType": "BASE"},
                {"scenarioId": "S3", "title": "T3", "description": "D", "scenarioType": "wild card"},
                {"scenarioId": "S4", "title": "T4", "description": "D", "scenarioType": "UNKNOWN"},
            ],
            "leadingIndicators": [],
        }
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        scenarios = result["scenarios"]
        assert scenarios[0]["scenarioType"] == "baseline"
        assert scenarios[1]["scenarioType"] == "baseline"  # BASE -> baseline
        assert scenarios[2]["scenarioType"] == "wildcard"  # wild card -> wildcard
        assert scenarios[3]["scenarioType"] == "baseline"  # unknown -> default

    def test_clamps_scenario_probabilities(self):
        """Test that scenario probabilities are clamped to [0.0, 1.0]."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "scenarioSummary": "S",
            "predeterminedElements": [],
            "keyUncertainties": [],
            "scenarios": [
                {"scenarioId": "S1", "title": "T", "description": "D", "scenarioType": "baseline", "probability": 1.5},
                {"scenarioId": "S2", "title": "T", "description": "D", "scenarioType": "alternative", "probability": -0.5},
                {"scenarioId": "S3", "title": "T", "description": "D", "scenarioType": "wildcard", "probability": "invalid"},
            ],
            "leadingIndicators": [],
        }
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        scenarios = result["scenarios"]
        assert 0.0 <= scenarios[0]["probability"] <= 1.0
        assert 0.0 <= scenarios[1]["probability"] <= 1.0
        assert 0.0 <= scenarios[2]["probability"] <= 1.0

    def test_sanitizes_leading_indicator_defaults(self):
        """Test that leading indicators with missing fields get defaults."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "scenarioSummary": "S",
            "predeterminedElements": [],
            "keyUncertainties": [],
            "scenarios": [],
            "leadingIndicators": [
                {"signalName": "信号1"},  # missing most fields
                {},  # completely empty
                {"priority": 10, "trend": "急速上升"},  # out of range
            ],
        }
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        indicators = result["leadingIndicators"]
        assert indicators[0]["signalName"] == "信号1"
        assert indicators[0]["priority"] == 3
        assert indicators[1]["signalName"] == ""
        assert indicators[2]["priority"] == 5  # clamped
        assert indicators[2]["trend"] == "稳定"  # invalid -> default
        assert len(result["scenarios"]) == 0

    def test_graceful_degradation_on_type_error(self):
        """Test graceful degradation on TypeError."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = TypeError("unexpected arg")
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        assert result is None

    def test_graceful_degradation_on_connection_error(self):
        """Test graceful degradation on connection error."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = ConnectionError("Connection refused")
        result = plan_scenarios(mock_client, {"weeklyNarrative": "叙事"})
        assert result is None

    @pytest.mark.integration
    def test_plan_scenarios_integration(self):
        """Integration test: requires DEEPSEEK_API_KEY."""
        import os

        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key or "dummy" in api_key.lower() or "pytest" in api_key.lower():
            pytest.skip("DEEPSEEK_API_KEY not set or is a dummy key")

        from chinese_scraper_utils import DeepSeekClient
        from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL_EMPIRICAL

        client = DeepSeekClient(
            DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_EMPIRICAL, thinking=False
        )
        synthesis = {
            "weeklyNarrative": "本周多个事件反映了资本在科技、劳动、金融三个领域的集中化趋势",
            "crossCuttingThemes": [
                {
                    "name": "平台资本对劳动者的成本转嫁",
                    "description": "平台企业通过调整抽成、定价等机制将运营成本转嫁给劳动者",
                    "relatedEventIds": ["evt-1", "evt-2"],
                    "significance": "结构性矛盾",
                }
            ],
            "trends": [
                {
                    "name": "政府监管力度加大",
                    "description": "监管部门对科技公司的介入在增加",
                    "direction": "上升",
                    "evidenceEventIds": ["evt-1"],
                }
            ],
            "contradictionsInMotion": [
                {
                    "contradiction": "资本积累与劳动者权益保护",
                    "opposingForces": "资本 vs 劳动者",
                    "eventsInvolved": ["evt-1", "evt-2"],
                    "currentState": "对抗激化",
                    "outlook": "短期继续激化",
                }
            ],
            "globalAssessment": "本周核心矛盾运动处于积累期",
            "dataGaps": ["缺乏具体信息"],
        }
        result = plan_scenarios(client, synthesis)
        assert result is not None, "Scenario planning should return a result"
        assert "scenarioSummary" in result
        assert "scenarios" in result
        assert isinstance(result["scenarios"], list)
        assert len(result["scenarios"]) > 0
        assert "leadingIndicators" in result
        for scenario in result["scenarios"]:
            assert "scenarioType" in scenario
            assert scenario["scenarioType"] in ("baseline", "alternative", "wildcard")
            assert "probability" in scenario
            assert 0.0 <= scenario["probability"] <= 1.0
