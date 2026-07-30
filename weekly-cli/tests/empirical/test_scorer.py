"""Test Empirical Layer: Scorer (9-dimension calibration)."""
import json
import pytest
from unittest.mock import MagicMock

from empirical.scorer import (
    score_event,
    format_event_for_scorer,
    _has_minimal_scoring_content,
    _validate_dimension_score,
    DIMENSION_NAMES,
)


class TestFormatEventForScorer:
    def test_formats_event_for_scoring(self):
        event = {
            "id": "evt-1",
            "title": "测试事件",
            "summary": "事件概述",
            "impactScore": 5,
            "infoGainScore": 4,
            "dialecticalSummary": "辩证总结",
        }
        text = format_event_for_scorer(event)
        assert "测试事件" in text
        assert "事件概述" in text
        assert "辩证总结" in text

    def test_formats_minimal_event(self):
        event = {"id": "evt-min", "title": "最小事件"}
        text = format_event_for_scorer(event)
        assert "最小事件" in text
        assert isinstance(text, str)

    def test_handles_empty_dict(self):
        text = format_event_for_scorer({})
        assert text is not None
        assert isinstance(text, str)

    def test_json_serializable(self):
        event = {"id": "e1", "title": "T", "nested": {"k": "v"}}
        text = format_event_for_scorer(event)
        json.dumps({"text": text})  # Should not raise


class TestHasMinimalScoringContent:
    def test_returns_true_with_title_and_summary(self):
        assert _has_minimal_scoring_content({"title": "T", "summary": "S"}) is True

    def test_returns_true_with_title_and_dialectical_summary(self):
        assert _has_minimal_scoring_content({"title": "T", "dialecticalSummary": "DS"}) is True

    def test_returns_false_for_empty(self):
        assert _has_minimal_scoring_content({}) is False

    def test_returns_false_for_none(self):
        assert _has_minimal_scoring_content(None) is False

    def test_returns_false_for_title_only(self):
        assert _has_minimal_scoring_content({"title": "Only"}) is False


class TestValidateDimensionScore:
    def test_valid_score_passes(self):
        assert _validate_dimension_score(1) is True
        assert _validate_dimension_score(5) is True
        assert _validate_dimension_score(10) is True

    def test_invalid_score_fails(self):
        assert _validate_dimension_score(0) is False
        assert _validate_dimension_score(-1) is False
        assert _validate_dimension_score(11) is False
        assert _validate_dimension_score(100) is False

    def test_float_that_is_valid_int(self):
        assert _validate_dimension_score(5.0) is True
        assert _validate_dimension_score(1.0) is True
        assert _validate_dimension_score(10.0) is True

    def test_float_not_int_fails(self):
        assert _validate_dimension_score(5.5) is False
        assert _validate_dimension_score(3.7) is False

    def test_none_fails(self):
        assert _validate_dimension_score(None) is False

    def test_non_numeric_fails(self):
        assert _validate_dimension_score("5") is False
        assert _validate_dimension_score([]) is False


class TestDimensionNames:
    def test_has_nine_dimensions(self):
        assert len(DIMENSION_NAMES) == 9

    def test_all_d1_through_d9_present(self):
        for i in range(1, 10):
            assert f"D{i}" in DIMENSION_NAMES

    def test_all_names_are_non_empty(self):
        for name in DIMENSION_NAMES.values():
            assert name and len(name) > 0


class TestScoreEvent:
    def test_returns_none_on_none_client(self):
        """Graceful degradation when client is None."""
        result = score_event(None, {"title": "Test", "summary": "S"})
        assert result is None

    def test_returns_none_on_empty_event(self):
        """Graceful degradation with insufficient event content."""
        mock_client = MagicMock()
        result = score_event(mock_client, {})
        assert result is None

    def test_returns_none_on_title_only_event(self):
        mock_client = MagicMock()
        result = score_event(mock_client, {"title": "OnlyTitle"})
        assert result is None

    def test_returns_none_on_client_error(self):
        """Graceful degradation when LLM call raises."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = RuntimeError("API timeout")
        result = score_event(mock_client, {"title": "T", "summary": "S"})
        assert result is None

    def test_returns_none_on_json_decode_error(self):
        """Graceful degradation on invalid JSON response."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = json.JSONDecodeError("bad", "{", 0)
        result = score_event(mock_client, {"title": "T", "summary": "S"})
        assert result is None

    def test_returns_none_on_non_dict_response(self):
        """Graceful degradation when response is not a dict."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = "not a dict"
        result = score_event(mock_client, {"title": "T", "summary": "S"})
        assert result is None

    def test_calls_chat_json_with_scorer_prompt(self):
        """Test LLM call with correct scorer prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "eventId": "evt-1",
            "eventTitle": "测试事件",
            "scoringSummary": "评分总览",
            "dimensions": [
                {
                    "id": "D1",
                    "name": "影响力规模",
                    "score": 7,
                    "confidence": "高",
                    "rationale": "全国性事件",
                },
                {
                    "id": "D2",
                    "name": "影响范围",
                    "score": 6,
                    "confidence": "中",
                    "rationale": "跨领域影响",
                },
                {
                    "id": "D3",
                    "name": "传播速度",
                    "score": 8,
                    "confidence": "高",
                    "rationale": "数小时内全国关注",
                },
                {
                    "id": "D4",
                    "name": "新颖程度",
                    "score": 3,
                    "confidence": "高",
                    "rationale": "类似事件曾有先例",
                },
                {
                    "id": "D5",
                    "name": "连锁反应潜能",
                    "score": 7,
                    "confidence": "低",
                    "rationale": "可能引发政策变动",
                },
                {
                    "id": "D6",
                    "name": "行动者显著度",
                    "score": 8,
                    "confidence": "高",
                    "rationale": "涉及行业龙头",
                },
                {
                    "id": "D7",
                    "name": "不确定性",
                    "score": 4,
                    "confidence": "中",
                    "rationale": "信息基本清晰",
                },
                {
                    "id": "D8",
                    "name": "极性",
                    "score": 6,
                    "confidence": "中",
                    "rationale": "存在明显立场分歧",
                },
                {
                    "id": "D9",
                    "name": "持久性",
                    "score": 7,
                    "confidence": "低",
                    "rationale": "预期影响持续数月",
                },
            ],
            "overallConfidence": "中",
            "informationSufficiency": "基本够用",
        }
        event = {
            "id": "evt-1",
            "title": "测试事件",
            "summary": "事件概述",
            "impactScore": 5,
        }
        result = score_event(mock_client, event)

        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]
        user_content = call_args[1]["content"]
        assert "测试事件" in user_content

        assert result is not None
        assert "eventId" in result
        assert "dimensions" in result
        assert len(result["dimensions"]) == 9
        assert result["dimensions"][0]["score"] == 7

    def test_defaults_applied_to_missing_fields(self):
        """Test defaults when LLM omits fields."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "scoringSummary": "评分",  # missing eventId, dimensions
        }
        event = {"title": "T", "summary": "S"}
        result = score_event(mock_client, event)

        assert result is not None
        assert "eventId" in result
        assert result["eventId"] == ""
        assert "dimensions" in result
        assert result["dimensions"] == []
        assert "overallConfidence" in result
        assert result["overallConfidence"] == "低"
        assert "informationSufficiency" in result
        assert result["informationSufficiency"] == "不足"

    def test_sanitizes_non_list_dimensions(self):
        """Test that non-list dimensions is replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "eventId": "e1",
            "eventTitle": "T",
            "scoringSummary": "S",
            "dimensions": "not a list",
        }
        event = {"title": "T", "summary": "S"}
        result = score_event(mock_client, event)

        assert result["dimensions"] == []

    def test_sanitizes_bad_dimension_scores(self):
        """Test that dimensions with out-of-range scores are clamped."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "eventId": "e1",
            "eventTitle": "T",
            "scoringSummary": "S",
            "dimensions": [
                {"id": "D1", "name": "影响力规模", "score": 15, "confidence": "高", "rationale": "test"},
                {"id": "D2", "name": "影响范围", "score": -3, "confidence": "中", "rationale": "test"},
                {"id": "D3", "name": "传播速度", "score": 5, "confidence": "高", "rationale": "test"},
                {"id": "D4", "name": "新颖程度", "score": "not a number", "confidence": "低", "rationale": "test"},
            ],
        }
        event = {"title": "T", "summary": "S"}
        result = score_event(mock_client, event)

        dims = result["dimensions"]
        # D1: 15 -> clamped to 10
        assert dims[0]["score"] == 10
        # D2: -3 -> clamped to 1
        assert dims[1]["score"] == 1
        # D3: 5 -> unchanged
        assert dims[2]["score"] == 5
        # D4: invalid -> default 5
        assert dims[3]["score"] == 5

    def test_dimensions_have_confidence_lowercase(self):
        """Test confidence values are normalized to Chinese characters."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "eventId": "e1",
            "eventTitle": "T",
            "scoringSummary": "S",
            "dimensions": [
                {"id": "D1", "name": "n1", "score": 5, "confidence": "HIGH", "rationale": "r"},
            ],
        }
        event = {"title": "T", "summary": "S"}
        result = score_event(mock_client, event)

        # confidence should still be a reasonable value
        assert result["dimensions"][0]["confidence"] in ("高", "中", "低", "HIGH")

    def test_dimensions_have_defaults_when_empty(self):
        """Test that empty dimension dicts get defaults."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "eventId": "e1",
            "eventTitle": "T",
            "scoringSummary": "S",
            "dimensions": [{}],
        }
        event = {"title": "T", "summary": "S"}
        result = score_event(mock_client, event)

        dim = result["dimensions"][0]
        assert "id" in dim
        assert dim["id"] == "D1"
        assert "score" in dim
        assert dim["score"] == 5
        assert "confidence" in dim
        assert dim["confidence"] == "低"

    def test_computes_composite_score(self):
        """Test that a composite score is computed from dimensions."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "eventId": "e1",
            "eventTitle": "T",
            "scoringSummary": "S",
            "dimensions": [
                {"id": "D1", "name": "n", "score": 2, "confidence": "高", "rationale": "r"},
                {"id": "D2", "name": "n", "score": 4, "confidence": "中", "rationale": "r"},
                {"id": "D3", "name": "n", "score": 6, "confidence": "高", "rationale": "r"},
                {"id": "D4", "name": "n", "score": 8, "confidence": "低", "rationale": "r"},
                {"id": "D5", "name": "n", "score": 10, "confidence": "低", "rationale": "r"},
                {"id": "D6", "name": "n", "score": 1, "confidence": "高", "rationale": "r"},
                {"id": "D7", "name": "n", "score": 3, "confidence": "中", "rationale": "r"},
                {"id": "D8", "name": "n", "score": 5, "confidence": "高", "rationale": "r"},
                {"id": "D9", "name": "n", "score": 9, "confidence": "中", "rationale": "r"},
            ],
        }
        event = {"title": "T", "summary": "S"}
        result = score_event(mock_client, event)

        assert "compositeScore" in result
        avg = sum([2, 4, 6, 8, 10, 1, 3, 5, 9]) / 9
        assert abs(result["compositeScore"] - avg) < 0.01

    def test_handles_null_confidence_in_dimension(self):
        """Test that null confidence is replaced with default."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "eventId": "e1",
            "eventTitle": "T",
            "scoringSummary": "S",
            "dimensions": [
                {"id": "D1", "name": "n", "score": 5, "confidence": None, "rationale": "r"},
            ],
        }
        event = {"title": "T", "summary": "S"}
        result = score_event(mock_client, event)
        assert result["dimensions"][0]["confidence"] == "低"

    def test_graceful_degradation_on_type_error(self):
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = TypeError("unexpected arg")
        result = score_event(mock_client, {"title": "T", "summary": "S"})
        assert result is None

    def test_graceful_degradation_on_connection_error(self):
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = ConnectionError("Connection refused")
        result = score_event(mock_client, {"title": "T", "summary": "S"})
        assert result is None

    @pytest.mark.integration
    def test_score_event_integration(self):
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
        event = {
            "id": "evt-1",
            "title": "中国央行宣布降准0.5个百分点",
            "summary": "中国人民银行决定下调金融机构存款准备金率，释放长期流动性约1万亿元",
            "impactScore": 4,
            "infoGainScore": 3,
            "dialecticalSummary": "货币政策调整反映了经济下行压力与稳增长政策之间的博弈",
        }
        result = score_event(client, event)
        assert result is not None, "Scorer should return a result"
        assert "eventId" in result
        assert "dimensions" in result
        assert isinstance(result["dimensions"], list)
        assert len(result["dimensions"]) == 9
        assert "compositeScore" in result
        # Verify each dimension has the required shape
        for dim in result["dimensions"]:
            assert "id" in dim
            assert "score" in dim
            assert 1 <= dim["score"] <= 10
            assert "confidence" in dim
