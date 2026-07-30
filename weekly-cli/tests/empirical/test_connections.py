"""Test Empirical Layer: Non-obvious Connection Discovery & PESTLE Matrix."""
import json
import pytest
from unittest.mock import MagicMock

from empirical.connections import (
    find_connections,
    _serialize_events,
    _has_minimal_event_data,
)


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
        assert isinstance(text, str)

    def test_json_serializable(self):
        events = [{"id": "e1", "title": "T"}]
        text = _serialize_events(events)
        json.dumps({"text": text})  # Should not raise


class TestHasMinimalEventData:
    def test_returns_true_with_two_events(self):
        assert _has_minimal_event_data([
            {"title": "事件一"},
            {"title": "事件二"},
        ]) is True

    def test_returns_false_with_one_event(self):
        assert _has_minimal_event_data([{"title": "Only"}]) is False

    def test_returns_false_with_empty_list(self):
        assert _has_minimal_event_data([]) is False

    def test_returns_false_with_none(self):
        assert _has_minimal_event_data(None) is False


class TestFindConnections:
    def test_returns_none_on_none_client(self):
        """Graceful degradation when client is None."""
        result = find_connections(None, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_returns_none_on_empty_events(self):
        """Graceful degradation with empty events."""
        mock_client = MagicMock()
        result = find_connections(mock_client, [])
        assert result is None

    def test_returns_none_on_single_event(self):
        """Graceful degradation with insufficient events."""
        mock_client = MagicMock()
        result = find_connections(mock_client, [{"title": "Only"}])
        assert result is None

    def test_returns_none_on_client_error(self):
        """Graceful degradation when LLM call raises."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = RuntimeError("API timeout")
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_returns_none_on_json_decode_error(self):
        """Graceful degradation on invalid JSON response."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = json.JSONDecodeError("bad", "{", 0)
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_returns_none_on_non_dict_response(self):
        """Graceful degradation when response is not a dict."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = "not a dict"
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_calls_chat_json_with_correct_prompt(self):
        """Test LLM call with correct connections prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "connectionSummary": "关联分析总述",
            "connections": [
                {
                    "connectionName": "价格战与监管关联",
                    "entityA": "AI价格战",
                    "entityB": "反垄断监管",
                    "connectionMechanism": "价格战引发市场份额集中",
                    "mediatingVariables": ["市场集中度"],
                    "significance": "揭示市场行为与政策响应的关联",
                    "confidence": "推测性",
                    "relatedEventIds": ["evt-1", "evt-2"],
                }
            ],
            "pestleMatrix": {
                "dominantDimension": "E",
                "dominantRationale": "经济维度主导",
                "dimensionInteractions": [
                    {
                        "fromDimension": "T",
                        "toDimension": "E",
                        "interactionDescription": "技术变革驱动经济结构调整",
                        "exampleEventIds": ["evt-1"],
                    }
                ],
                "eventImpacts": [
                    {
                        "eventId": "evt-1",
                        "eventTitle": "事件一",
                        "politicalImpact": "政治影响",
                        "economicImpact": "经济影响",
                        "socialImpact": "社会影响",
                        "technologicalImpact": "技术影响",
                        "legalImpact": "法律影响",
                        "environmentalImpact": "环境影响",
                        "overallAssessment": "总体评估",
                    }
                ],
            },
            "shortestPathLinks": [
                {
                    "sourceEventId": "evt-1",
                    "targetEventId": "evt-3",
                    "pathDescription": "经由中介事件evt-2连接",
                    "intermediateNodes": ["evt-2"],
                    "pathStrength": "中",
                    "networkSignificance": "关键路径",
                }
            ],
            "centralEvents": [
                {
                    "eventId": "evt-1",
                    "centralityRank": 1,
                    "rationale": "最核心节点",
                    "connectedEventIds": ["evt-2", "evt-3"],
                }
            ],
        }
        events = [
            {"id": "evt-1", "title": "事件一", "summary": "概述一"},
            {"id": "evt-2", "title": "事件二", "summary": "概述二"},
        ]
        result = find_connections(mock_client, events)

        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]
        user_content = call_args[1]["content"]
        assert "事件一" in user_content
        assert "事件二" in user_content

        assert result is not None
        assert "connectionSummary" in result
        assert "connections" in result
        assert len(result["connections"]) == 1
        assert result["connections"][0]["connectionName"] == "价格战与监管关联"

        assert "pestleMatrix" in result
        pm = result["pestleMatrix"]
        assert "dominantDimension" in pm
        assert "dimensionInteractions" in pm
        assert "eventImpacts" in pm
        assert len(pm["eventImpacts"]) == 1

        assert "shortestPathLinks" in result
        assert "centralEvents" in result

    def test_defaults_applied_to_missing_fields(self):
        """Test defaults when LLM omits fields from response."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "connectionSummary": "总述",
            # connections, pestleMatrix etc. missing
        }
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is not None
        assert result["connections"] == []
        assert result["shortestPathLinks"] == []
        assert result["centralEvents"] == []

    def test_sanitizes_non_dict_pestle_matrix(self):
        """Test that non-dict pestleMatrix is replaced with default."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "connectionSummary": "S",
            "connections": [],
            "pestleMatrix": "not a dict",
        }
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert isinstance(result["pestleMatrix"], dict)
        assert result["pestleMatrix"]["dimensionInteractions"] == []

    def test_sanitizes_non_list_fields(self):
        """Test that non-list fields are replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "connectionSummary": "S",
            "connections": "not a list",
            "pestleMatrix": {
                "dominantDimension": "E",
                "dominantRationale": "R",
                "dimensionInteractions": "not a list",
                "eventImpacts": "not a list",
            },
            "shortestPathLinks": "not a list",
            "centralEvents": "not a list",
        }
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result["connections"] == []
        assert result["pestleMatrix"]["dimensionInteractions"] == []
        assert result["pestleMatrix"]["eventImpacts"] == []
        assert result["shortestPathLinks"] == []
        assert result["centralEvents"] == []

    def test_sanitizes_connection_defaults(self):
        """Test that connections with missing fields get defaults."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "connectionSummary": "S",
            "connections": [
                {"connectionName": "C1"},  # missing most fields
                {},  # completely empty
            ],
            "pestleMatrix": {
                "dominantDimension": "E", "dominantRationale": "R",
                "dimensionInteractions": [], "eventImpacts": [],
            },
            "shortestPathLinks": [],
            "centralEvents": [],
        }
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        conns = result["connections"]
        assert conns[0]["connectionName"] == "C1"
        assert conns[0]["entityA"] == ""
        assert conns[0]["confidence"] == "推测性"
        assert conns[1]["connectionName"] == ""
        assert conns[1]["confidence"] == "推测性"

    def test_handles_empty_pestle_interactions_and_impacts(self):
        """Test handling of empty PESTLE sub-lists."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "connectionSummary": "S",
            "connections": [],
            "pestleMatrix": {
                "dominantDimension": "E",
                "dominantRationale": "R",
                "dimensionInteractions": [],
                "eventImpacts": [],
            },
            "shortestPathLinks": [],
            "centralEvents": [],
        }
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result["pestleMatrix"]["dimensionInteractions"] == []
        assert result["pestleMatrix"]["eventImpacts"] == []

    def test_graceful_degradation_on_type_error(self):
        """Test graceful degradation on TypeError."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = TypeError("unexpected arg")
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    def test_graceful_degradation_on_connection_error(self):
        """Test graceful degradation on connection error."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = ConnectionError("Connection refused")
        result = find_connections(mock_client, [
            {"title": "T1", "summary": "S1"},
            {"title": "T2", "summary": "S2"},
        ])
        assert result is None

    @pytest.mark.integration
    def test_find_connections_integration(self):
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
                "summary": "中国人民银行决定下调金融机构存款准备金率",
                "impactScore": 4,
                "dialecticalSummary": "货币政策调整反映了经济下行压力与稳增长政策之间的博弈",
            },
            {
                "id": "evt-2",
                "title": "多家AI公司宣布大幅降价",
                "summary": "AI行业价格战持续升温",
                "impactScore": 5,
                "dialecticalSummary": "价格战反映了技术商业化加速期的竞争白热化",
            },
        ]
        result = find_connections(client, events)
        assert result is not None, "Connection analysis should return a result"
        assert "connectionSummary" in result
        assert "connections" in result
        assert "pestleMatrix" in result
        assert isinstance(result["connections"], list)
        assert isinstance(result["shortestPathLinks"], list)
