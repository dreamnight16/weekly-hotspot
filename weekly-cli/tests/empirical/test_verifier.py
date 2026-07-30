"""Test Empirical Layer: Evidence Verifier."""
import json
import pytest
from unittest.mock import MagicMock

from empirical.verifier import (
    verify_evidence,
    format_event_for_verifier,
    _has_minimal_event_content,
)


class TestFormatEventForVerifier:
    def test_formats_event_with_all_fields(self):
        event = {
            "id": "evt-1",
            "title": "测试事件",
            "summary": "事件概述内容",
            "impactScore": 4,
            "infoGainScore": 3,
            "evidence": [
                {
                    "id": "ev-1",
                    "sourceType": "官媒",
                    "sourceName": "人民日报",
                    "content": "报道内容",
                    "authenticity": "真实",
                }
            ],
            "timeline": [
                {
                    "id": "tl-1",
                    "time": "2026-01-01",
                    "title": "节点1",
                    "description": "描述",
                }
            ],
            "dialecticalSummary": "辩证总结",
        }
        text = format_event_for_verifier(event)
        assert "测试事件" in text
        assert "事件概述内容" in text
        assert "人民日报" in text
        assert "辩证总结" in text

    def test_formats_minimal_event(self):
        event = {
            "id": "evt-min",
            "title": "最小事件",
        }
        text = format_event_for_verifier(event)
        assert "最小事件" in text
        assert "evt-min" in text

    def test_handles_empty_dict(self):
        text = format_event_for_verifier({})
        assert text is not None
        assert isinstance(text, str)

    def test_truncates_long_content(self):
        event = {
            "id": "evt-long",
            "title": "长内容事件",
            "summary": "X" * 5000,
        }
        text = format_event_for_verifier(event)
        assert len(text) < 8000  # Should be within reasonable bounds

    def test_json_serializable_output(self):
        """Verify output is valid JSON serializable (used inside prompt)."""
        event = {"id": "evt-1", "title": "Test", "nested": {"key": "value"}}
        text = format_event_for_verifier(event)
        # Should not raise
        json.dumps({"text": text})


class TestHasMinimalEventContent:
    def test_returns_true_for_event_with_title_and_summary(self):
        event = {"title": "Test", "summary": "Summary text"}
        assert _has_minimal_event_content(event) is True

    def test_returns_true_for_event_with_evidence(self):
        event = {"title": "Test", "evidence": [{"id": "e1"}]}
        assert _has_minimal_event_content(event) is True

    def test_returns_true_for_event_with_dialectical_summary(self):
        event = {"title": "Event", "dialecticalSummary": "Some summary"}
        assert _has_minimal_event_content(event) is True

    def test_returns_false_for_empty_dict(self):
        assert _has_minimal_event_content({}) is False

    def test_returns_false_for_none(self):
        assert _has_minimal_event_content(None) is False

    def test_returns_false_for_title_only(self):
        event = {"title": "Only title"}
        assert _has_minimal_event_content(event) is False


class TestVerifyEvidence:
    def test_returns_none_on_none_client(self):
        """Test graceful degradation when client is None."""
        result = verify_evidence(client=None, event={"title": "Test", "summary": "S"})
        assert result is None

    def test_returns_none_on_empty_event(self):
        """Test graceful degradation when event has insufficient content."""
        mock_client = MagicMock()
        result = verify_evidence(mock_client, event={})
        assert result is None

    def test_returns_none_on_title_only_event(self):
        """Test graceful degradation when event only has title."""
        mock_client = MagicMock()
        result = verify_evidence(mock_client, event={"title": "OnlyTitle"})
        assert result is None

    def test_returns_none_on_client_error(self):
        """Test graceful degradation when LLM call raises an exception."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = RuntimeError("API timeout")
        result = verify_evidence(
            mock_client,
            event={"title": "Test", "summary": "Summary", "evidence": [{"id": "e1", "content": "Evidence"}]}
        )
        assert result is None

    def test_returns_none_on_json_decode_error(self):
        """Test graceful degradation when LLM returns invalid JSON."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = json.JSONDecodeError("bad", "{", 0)
        result = verify_evidence(
            mock_client,
            event={"title": "Test", "summary": "Summary", "evidence": []}
        )
        assert result is None

    def test_returns_none_on_non_dict_response(self):
        """Test graceful degradation when LLM returns a non-dict."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = ["not", "a", "dict"]
        result = verify_evidence(
            mock_client,
            event={"title": "Test", "summary": "Summary"}
        )
        assert result is None

    def test_calls_chat_json_with_verifier_prompt(self):
        """Test that LLM is called with correct verifier prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "verificationSummary": "证据质量良好",
            "sourceGrades": [
                {
                    "sourceName": "人民日报",
                    "sourceType": "官媒",
                    "reliability": "B",
                    "credibility": 2,
                    "rationale": "该来源在此事件中报道属实",
                    "impactOnAnalysis": "支撑核心事实断言",
                    "relatedClaimIds": ["assert-1"],
                }
            ],
            "verificationResults": [
                {
                    "claimId": "assert-1",
                    "claim": "核心事实断言",
                    "claimType": "事实断言",
                    "verificationStatus": "完全验证",
                    "independentSources": ["人民日报", "新华社"],
                    "contradictorySources": [],
                    "verificationNote": "多方独立确认",
                    "confidence": "HIGH",
                }
            ],
            "corroborationMatrix": [
                {
                    "factStatement": "事实陈述",
                    "sources": ["人民日报", "新华社"],
                    "independentCount": 2,
                    "sourceDiversity": "中",
                    "crossConsistency": "一致",
                }
            ],
            "achResults": [
                {
                    "achId": "ach-1",
                    "proposition": "解释命题",
                    "eventId": "evt-1",
                    "hypotheses": [
                        {
                            "hypothesisLabel": "H0",
                            "description": "主假设",
                            "consistencyWithEvidence": "吻合",
                            "contradictionsWithEvidence": "无",
                        },
                        {
                            "hypothesisLabel": "H1",
                            "description": "竞争假设1",
                            "consistencyWithEvidence": "部分吻合",
                            "contradictionsWithEvidence": "与证据X矛盾",
                        },
                        {
                            "hypothesisLabel": "H2",
                            "description": "竞争假设2",
                            "consistencyWithEvidence": "较弱",
                            "contradictionsWithEvidence": "与多项证据矛盾",
                        },
                    ],
                    "diagnosticEvidence": [
                        {
                            "evidenceDescription": "诊断证据",
                            "discriminatoryPower": "强",
                        }
                    ],
                    "relativeCredibilityRanking": "H0, H1, H2",
                    "rankingRationale": "排序理由",
                }
            ],
            "informationGaps": [
                {
                    "gapDescription": "缺少事件直接参与方的说法",
                    "severity": "MEDIUM",
                    "possibleSources": "官方通报或采访",
                }
            ],
        }
        event = {
            "id": "evt-1",
            "title": "测试事件",
            "summary": "事件概述",
            "evidence": [
                {"id": "ev-1", "sourceType": "官媒", "sourceName": "人民日报", "content": "报道"}
            ],
        }
        result = verify_evidence(mock_client, event)

        # Verify chat_json was called
        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]  # messages
        user_content = call_args[1]["content"]
        assert "测试事件" in user_content

        # Verify result structure
        assert result is not None
        assert "verificationSummary" in result
        assert "sourceGrades" in result
        assert len(result["sourceGrades"]) == 1
        assert result["sourceGrades"][0]["reliability"] == "B"
        assert "achResults" in result
        assert len(result["achResults"]) == 1
        assert "corroborationMatrix" in result

    def test_defaults_applied_to_missing_fields(self):
        """Test defaults applied when LLM omits optional fields."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "verificationSummary": "证据审查总述",
            # sourceGrades missing
            # verificationResults missing
            # corroborationMatrix missing
            # achResults missing
            # informationGaps missing
        }
        event = {
            "title": "Test",
            "summary": "Summary",
            "evidence": [{"id": "e1", "content": "Evidence content"}],
        }
        result = verify_evidence(mock_client, event)
        assert result is not None
        assert "sourceGrades" in result
        assert result["sourceGrades"] == []
        assert "verificationResults" in result
        assert result["verificationResults"] == []
        assert "corroborationMatrix" in result
        assert result["corroborationMatrix"] == []
        assert "achResults" in result
        assert result["achResults"] == []
        assert "informationGaps" in result
        assert result["informationGaps"] == []

    def test_sanitizes_non_list_fields(self):
        """Test that non-list fields are replaced with empty lists."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "verificationSummary": "test",
            "sourceGrades": "not a list",
            "verificationResults": 123,
            "corroborationMatrix": None,
            "achResults": {"wrong": "type"},
            "informationGaps": "also wrong",
        }
        event = {"title": "Test", "summary": "Summary"}
        result = verify_evidence(mock_client, event)
        assert result is not None
        assert result["sourceGrades"] == []
        assert result["verificationResults"] == []
        assert result["corroborationMatrix"] == []
        assert result["achResults"] == []
        assert result["informationGaps"] == []

    def test_handles_event_with_timeline_and_edges(self):
        """Test verifier handles a full event with timeline and edges."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "verificationSummary": "测试",
            "sourceGrades": [],
            "verificationResults": [
                {
                    "claimId": "assert-1",
                    "claim": "断言",
                    "claimType": "事实断言",
                    "verificationStatus": "单源依赖",
                    "independentSources": ["来源A"],
                    "contradictorySources": [],
                    "verificationNote": "仅一个来源",
                    "confidence": "LOW",
                }
            ],
            "corroborationMatrix": [],
            "achResults": [],
            "informationGaps": [],
        }
        event = {
            "id": "evt-complex",
            "title": "复杂事件",
            "summary": "概述",
            "impactScore": 5,
            "infoGainScore": 4,
            "timeline": [
                {
                    "id": "tl-1",
                    "time": "2026-01-01T10:00:00",
                    "title": "节点1",
                    "description": "描述1",
                    "evidenceRefs": ["ev-1"],
                },
                {
                    "id": "tl-2",
                    "time": "2026-01-02T10:00:00",
                    "title": "节点2",
                    "description": "描述2",
                    "evidenceRefs": ["ev-2"],
                },
            ],
            "evidence": [
                {"id": "ev-1", "sourceType": "官媒", "sourceName": "来源A", "content": "证据1"},
                {"id": "ev-2", "sourceType": "自媒体", "sourceName": "来源B", "content": "证据2"},
            ],
            "edges": [
                {"from": "tl-1", "to": "tl-2", "type": "因果", "description": "后续发展"},
            ],
            "dialecticalSummary": "辩证总结内容",
        }
        result = verify_evidence(mock_client, event)
        assert result is not None
        assert "verificationResults" in result
        assert len(result["verificationResults"]) == 1

    def test_graceful_degradation_on_large_event(self):
        """Test that very large events don't crash the verifier."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "verificationSummary": "test",
            "sourceGrades": [],
            "verificationResults": [],
            "corroborationMatrix": [],
            "achResults": [],
            "informationGaps": [],
        }
        event = {
            "title": "Large Event",
            "summary": "X" * 10000,
            "dialecticalSummary": "Y" * 5000,
            "evidence": [
                {"id": f"ev-{i}", "content": f"证据{i}"} for i in range(100)
            ],
        }
        result = verify_evidence(mock_client, event)
        assert result is not None

    @pytest.mark.integration
    def test_verify_evidence_integration(self):
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
            "title": "OpenAI宣布GPT-5价格大幅下调90%",
            "summary": "OpenAI发布新一代模型并大幅降价，引发AI行业价格战",
            "impactScore": 4,
            "infoGainScore": 3,
            "evidence": [
                {
                    "id": "ev-1",
                    "sourceType": "官媒",
                    "sourceName": "新华社",
                    "sourceUrl": "https://example.com/news",
                    "content": "OpenAI宣布即日起大幅下调API价格，部分模型降幅达90%",
                    "authenticity": "真实",
                    "aiReason": "官方发布，多方确认",
                    "classBias": "待判断",
                }
            ],
            "dialecticalSummary": "AI资本通过价格战加速行业洗牌，体现了技术垄断资本对市场的控制",
        }
        result = verify_evidence(client, event)
        assert result is not None, "Verifier should return a result"
        assert "verificationSummary" in result
        assert "sourceGrades" in result
        assert isinstance(result["sourceGrades"], list)
        assert "achResults" in result
        assert isinstance(result["achResults"], list)
