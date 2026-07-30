"""Test Empirical Layer: Causal Loop Diagrams & System Archetype Matching."""
import json
import pytest
from unittest.mock import MagicMock

from empirical.causal import build_causal_loop, _serialize_events, _has_minimal_event_data


class TestSerializeEvents:
    def test_serializes_events(self):
        events = [
            {"id": "evt-1", "title": "事件一", "summary": "概述一"},
            {"id": "evt-2", "title": "事件二", "summary": "概述二"},
        ]
        text = _serialize_events(events)
        assert "事件一" in text
        assert "事件二" in text
        assert isinstance(text, str)

    def test_handles_empty_list(self):
        text = _serialize_events([])
        assert text is not None
        assert isinstance(text, str)

    def test_truncates_long_fields(self):
        events = [{"id": "e1", "title": "T", "summary": "x" * 3000}]
        text = _serialize_events(events)
        assert len(text) < 3500  # Should be truncated

    def test_json_serializable(self):
        events = [{"id": "e1", "title": "T", "nested": {"k": "v"}}]
        text = _serialize_events(events)
        json.dumps({"text": text})  # Should not raise


class TestHasMinimalEventData:
    def test_returns_true_with_two_events(self):
        assert _has_minimal_event_data([
            {"title": "事件一", "summary": "S"},
            {"title": "事件二", "summary": "S"},
        ]) is True

    def test_returns_false_with_one_event(self):
        assert _has_minimal_event_data([{"title": "Only"}]) is False

    def test_returns_false_with_empty_list(self):
        assert _has_minimal_event_data([]) is False

    def test_returns_false_with_none(self):
        assert _has_minimal_event_data(None) is False

    def test_returns_false_with_non_list(self):
        assert _has_minimal_event_data({"title": "T"}) is False

    def test_returns_false_with_missing_titles(self):
        assert _has_minimal_event_data([{"title": "T1"}, {"summary": "NoTitle"}]) is False

    def test_returns_false_with_empty_title(self):
        assert _has_minimal_event_data([
            {"title": "T1"},
            {"title": ""},
        ]) is False


class TestBuildCausalLoop:
    def test_returns_none_on_none_client(self):
        """Graceful degradation when client is None."""
        result = build_causal_loop(None, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_returns_none_on_empty_events(self):
        """Graceful degradation with empty events."""
        mock_client = MagicMock()
        result = build_causal_loop(mock_client, [])
        assert result is None

    def test_returns_none_on_single_event(self):
        """Graceful degradation with insufficient events."""
        mock_client = MagicMock()
        result = build_causal_loop(mock_client, [{"title": "Only"}])
        assert result is None

    def test_returns_none_on_client_error(self):
        """Graceful degradation when LLM call raises."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = RuntimeError("API timeout")
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_returns_none_on_json_decode_error(self):
        """Graceful degradation on invalid JSON response."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = json.JSONDecodeError("bad", "{", 0)
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_returns_none_on_non_dict_response(self):
        """Graceful degradation when response is not a dict."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = "not a dict"
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_calls_chat_json_with_correct_prompt(self):
        """Test LLM call with correct causal prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "causalSummary": "因果分析总述",
            "causalLoopDiagram": {
                "nodes": ["资本集中", "劳动力成本", "监管力度"],
                "positiveFeedbackLoops": [
                    {
                        "loopName": "资本集中加速",
                        "description": "资本集中导致市场支配力增强",
                        "involvedNodes": ["资本集中", "市场支配力"],
                        "strength": "强",
                        "relatedEventIds": ["evt-1"],
                    }
                ],
                "negativeFeedbackLoops": [
                    {
                        "loopName": "监管抑制",
                        "description": "监管力度增加抑制资本过度集中",
                        "involvedNodes": ["监管力度", "资本集中"],
                        "strength": "中",
                        "relatedEventIds": ["evt-2"],
                    }
                ],
                "keyLeveragePoints": [
                    {
                        "nodeName": "监管力度",
                        "interventionDescription": "加强反垄断监管",
                        "expectedImpact": "减缓资本集中趋势",
                        "difficulty": "中",
                    }
                ],
            },
            "systemArchetypes": [
                {
                    "archetypeType": "LimitsToGrowth",
                    "patternName": "增长极限",
                    "description": "资本扩张遇到监管和资源约束",
                    "matchingRationale": "多个事件显示增长与约束之间的张力",
                    "currentStage": "发展期",
                    "structuralFeatures": "增长引擎与约束因素的互动",
                    "relatedEventIds": ["evt-1", "evt-2"],
                }
            ],
        }
        events = [
            {"id": "evt-1", "title": "事件一", "summary": "概述一", "classAnalysis": {"contradiction": "劳资矛盾"}},
            {"id": "evt-2", "title": "事件二", "summary": "概述二", "classAnalysis": {"contradiction": "资本与政策"}},
        ]
        result = build_causal_loop(mock_client, events)

        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]
        user_content = call_args[1]["content"]
        assert "事件一" in user_content
        assert "事件二" in user_content

        assert result is not None
        assert "causalSummary" in result
        assert "causalLoopDiagram" in result
        assert "systemArchetypes" in result

        cld = result["causalLoopDiagram"]
        assert "nodes" in cld
        assert "positiveFeedbackLoops" in cld
        assert "negativeFeedbackLoops" in cld
        assert len(cld["positiveFeedbackLoops"]) == 1
        assert len(cld["negativeFeedbackLoops"]) == 1

        archetypes = result["systemArchetypes"]
        assert len(archetypes) == 1
        assert archetypes[0]["archetypeType"] == "LimitsToGrowth"

    def test_defaults_applied_to_missing_fields(self):
        """Test defaults when LLM omits fields from response."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "causalSummary": "总述",
            # causalLoopDiagram missing
        }
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is not None
        assert "causalSummary" in result
        assert "causalLoopDiagram" in result
        assert "systemArchetypes" in result
        assert result["causalLoopDiagram"]["nodes"] == []
        assert result["systemArchetypes"] == []

    def test_sanitizes_non_dict_causal_loop_diagram(self):
        """Test that non-dict causalLoopDiagram is replaced with default."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "causalSummary": "S",
            "causalLoopDiagram": "not a dict",
        }
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result["causalLoopDiagram"]["nodes"] == []

    def test_sanitizes_non_list_archetypes(self):
        """Test that non-list archetypes is replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "causalSummary": "S",
            "causalLoopDiagram": {"nodes": [], "positiveFeedbackLoops": [], "negativeFeedbackLoops": [], "keyLeveragePoints": []},
            "systemArchetypes": "not a list",
        }
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result["systemArchetypes"] == []

    def test_sanitizes_archetype_type(self):
        """Test that archetype types are normalized."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "causalSummary": "S",
            "causalLoopDiagram": {"nodes": [], "positiveFeedbackLoops": [], "negativeFeedbackLoops": [], "keyLeveragePoints": []},
            "systemArchetypes": [
                {"archetypeType": "FixesThatFail", "patternName": "P", "description": "D"},
                {"archetypeType": "fixes that fail", "patternName": "P", "description": "D"},
                {"archetypeType": "UNKNOWN_TYPE", "patternName": "P", "description": "D"},
                {"archetypeType": "tragedy of the commons", "patternName": "P", "description": "D"},
            ],
        }
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        archetypes = result["systemArchetypes"]
        assert archetypes[0]["archetypeType"] == "FixesThatFail"
        assert archetypes[1]["archetypeType"] == "FixesThatFail"
        assert archetypes[2]["archetypeType"] == "LimitsToGrowth"  # default
        assert archetypes[3]["archetypeType"] == "TragedyOfCommons"

    def test_handles_empty_archetype_dicts(self):
        """Test that empty archetype dicts get defaults."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "causalSummary": "S",
            "causalLoopDiagram": {"nodes": [], "positiveFeedbackLoops": [], "negativeFeedbackLoops": [], "keyLeveragePoints": []},
            "systemArchetypes": [{}],
        }
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        arch = result["systemArchetypes"][0]
        assert arch["archetypeType"] == "LimitsToGrowth"
        assert arch["patternName"] == ""
        assert arch["description"] == ""

    def test_sanitizes_feedback_loop_defaults(self):
        """Test that feedback loops with missing fields get defaults."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "causalSummary": "S",
            "causalLoopDiagram": {
                "nodes": [],
                "positiveFeedbackLoops": [{"loopName": "L"}],  # missing fields
                "negativeFeedbackLoops": [{}],
                "keyLeveragePoints": [{}],
            },
            "systemArchetypes": [],
        }
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        cld = result["causalLoopDiagram"]
        assert cld["positiveFeedbackLoops"][0]["loopName"] == "L"
        assert cld["positiveFeedbackLoops"][0]["strength"] == "中"
        assert cld["negativeFeedbackLoops"][0]["strength"] == "中"
        assert cld["keyLeveragePoints"][0]["difficulty"] == "中"
        assert cld["positiveFeedbackLoops"][0]["involvedNodes"] == []

    def test_graceful_degradation_on_type_error(self):
        """Test graceful degradation on TypeError."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = TypeError("unexpected arg")
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_graceful_degradation_on_connection_error(self):
        """Test graceful degradation on connection error."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = ConnectionError("Connection refused")
        result = build_causal_loop(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    @pytest.mark.integration
    def test_build_causal_loop_integration(self):
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
        events = [
            {
                "id": "evt-1",
                "title": "中国央行宣布降准0.5个百分点",
                "summary": "中国人民银行决定下调金融机构存款准备金率，释放长期流动性约1万亿元",
                "impactScore": 4,
                "infoGainScore": 3,
                "dialecticalSummary": "货币政策调整反映了经济下行压力与稳增长政策之间的博弈",
                "classAnalysis": {"contradiction": "货币政策与经济增长"},
            },
            {
                "id": "evt-2",
                "title": "多家AI公司宣布大幅降价",
                "summary": "AI行业价格战持续升温，多家公司宣布降价幅度超过50%",
                "impactScore": 5,
                "infoGainScore": 4,
                "dialecticalSummary": "价格战反映了技术商业化加速期的竞争白热化",
                "classAnalysis": {"contradiction": "资本扩张与市场竞争"},
            },
        ]
        result = build_causal_loop(client, events)
        assert result is not None, "Causal analysis should return a result"
        assert "causalSummary" in result
        assert "causalLoopDiagram" in result
        assert "systemArchetypes" in result
        cld = result["causalLoopDiagram"]
        assert isinstance(cld.get("nodes"), list)
        assert isinstance(cld.get("positiveFeedbackLoops"), list)
        assert isinstance(cld.get("negativeFeedbackLoops"), list)
        archetypes = result["systemArchetypes"]
        assert isinstance(archetypes, list)
        if archetypes:
            for arch in archetypes:
                assert "archetypeType" in arch
                assert arch["archetypeType"] in ("FixesThatFail", "LimitsToGrowth", "ShiftingTheBurden", "TragedyOfCommons")
