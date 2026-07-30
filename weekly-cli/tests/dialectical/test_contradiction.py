"""Test Phase 2: Contradiction Identification."""
import pytest
from unittest.mock import MagicMock

from dialectical.contradiction import build_contradiction_context, identify_contradictions


class TestBuildContradictionContext:
    def test_formats_events_with_all_fields(self):
        events = [
            {
                "id": "evt-1",
                "title": "测试事件",
                "materialContent": "测试物质内容",
                "summary": "测试概述",
            }
        ]
        ctx = build_contradiction_context(events)
        assert "evt-1" in ctx
        assert "测试事件" in ctx
        assert "测试物质内容" in ctx
        assert "测试概述" in ctx

    def test_handles_empty_list(self):
        ctx = build_contradiction_context([])
        assert ctx == ""

    def test_handles_missing_fields(self):
        events = [{"id": "evt-1"}]  # no title, summary, materialContent
        ctx = build_contradiction_context(events)
        assert "evt-1" in ctx
        assert "(无标题)" in ctx

    def test_handles_none_summary_and_material(self):
        events = [
            {"id": "evt-1", "title": "Title", "summary": None, "materialContent": None}
        ]
        ctx = build_contradiction_context(events)
        assert "Title" in ctx
        # summary and materialContent lines should not appear when None
        assert "概述" not in ctx
        assert "物质内容" not in ctx

    def test_truncates_long_content(self):
        events = [
            {
                "id": "evt-1",
                "title": "Event",
                "summary": "S" * 400,
                "materialContent": "M" * 600,
            }
        ]
        ctx = build_contradiction_context(events)
        # Summary truncated to 300 chars
        summary_line = [l for l in ctx.split("\n") if "概述" in l]
        if summary_line:
            assert len(summary_line[0].strip()) <= 300 + len("  概述: ")
        # MaterialContent truncated to 500 chars
        material_line = [l for l in ctx.split("\n") if "物质内容" in l]
        if material_line:
            assert len(material_line[0].strip()) <= 500 + len("  物质内容: ")

    def test_multiple_events(self):
        events = [
            {"id": "evt-1", "title": "事件A", "summary": "概述A"},
            {"id": "evt-2", "title": "事件B", "summary": "概述B"},
        ]
        ctx = build_contradiction_context(events)
        assert "事件A" in ctx
        assert "事件B" in ctx
        assert "[事件 1]" in ctx
        assert "[事件 2]" in ctx


class TestIdentifyContradictions:
    def test_empty_events_returns_default(self):
        result = identify_contradictions(client=None, events=[])
        assert result == {
            "phaseSummary": "无事件可供矛盾分析",
            "events": [],
            "overallContradictionLandscape": "",
            "interestStructures": [],
            "classPositions": [],
            "nineDimScores": {},
            "competingHypotheses": [],
        }

    def test_none_events_returns_empty_list(self):
        """Test that None events is replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": None,
        }
        result = identify_contradictions(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert result["events"] == []

    def test_non_list_events_returns_empty_list(self):
        """Test that non-list events is replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": "error string",
        }
        result = identify_contradictions(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert result["events"] == []

    def test_defaults_applied_to_events(self):
        """Test that id, title, and isDirectExpression defaults are applied."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [
                {"summary": "Only summary"},  # no id, no title
                {
                    "id": "custom-id",
                    "title": "Custom Title",
                    "summary": "S2",
                    "isDirectExpression": False,
                },
            ],
        }
        result = identify_contradictions(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        events = result["events"]
        assert len(events) == 2
        # First event: defaults applied
        assert events[0]["id"] == "evt-1"
        assert events[0]["title"] == "(无标题)"
        assert events[0]["isDirectExpression"] is True
        # Second event: original values preserved
        assert events[1]["id"] == "custom-id"
        assert events[1]["title"] == "Custom Title"
        assert events[1]["isDirectExpression"] is False

    def test_none_top_level_fields_defaulted(self):
        """Test that None top-level fields get default values."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
            "interestStructures": None,
            "classPositions": None,
            "nineDimScores": None,
            "competingHypotheses": None,
        }
        result = identify_contradictions(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert result["interestStructures"] == []
        assert result["classPositions"] == []
        assert result["nineDimScores"] == {}
        assert result["competingHypotheses"] == []

    def test_calls_chat_json_with_correct_prompt(self):
        """Test that the LLM is called with formatted contradiction prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
        }
        events = [
            {
                "id": "evt-1",
                "title": "AI大模型价格战",
                "materialContent": "科技资本通过价格战清洗中小竞争者",
                "summary": "多家科技巨头宣布大幅下调大模型API价格",
            }
        ]
        identify_contradictions(mock_client, events)

        # Verify chat_json was called
        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]  # messages
        user_content = call_args[1]["content"]
        assert "AI大模型价格战" in user_content
        assert "科技资本通过价格战清洗中小竞争者" in user_content

    def test_includes_phase_summary_in_result(self):
        """Test that phaseSummary is passed through from LLM response."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "本周矛盾主要集中在科技资本竞争领域",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
        }
        result = identify_contradictions(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert "本周矛盾主要集中在科技资本竞争领域" in result["phaseSummary"]

    def test_non_dict_events_skipped(self):
        """Test that non-dict entries in events list are skipped."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [
                "not a dict",
                {"id": "evt-1", "title": "Valid", "summary": "S"},
                123,
            ],
        }
        result = identify_contradictions(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert len(result["events"]) == 1
        assert result["events"][0]["title"] == "Valid"

    @pytest.mark.integration
    def test_identify_contradictions_integration(self):
        """Integration test: requires DEEPSEEK_API_KEY."""
        import os

        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key or "dummy" in api_key.lower() or "pytest" in api_key.lower():
            pytest.skip("DEEPSEEK_API_KEY not set or is a dummy key")
        from chinese_scraper_utils import DeepSeekClient
        from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL_DIALECTICAL

        client = DeepSeekClient(
            DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_DIALECTICAL, thinking=True
        )
        events = [
            {
                "id": "evt-1",
                "title": "AI大模型价格战全面爆发",
                "materialContent": "科技资本通过价格战清洗中小竞争者",
                "summary": "多家科技巨头宣布大幅下调大模型API价格",
            }
        ]
        result = identify_contradictions(client, events)
        assert "events" in result
        assert len(result["events"]) >= 1
        e = result["events"][0]
        assert "id" in e
        assert "title" in e
        assert "summary" in e
        # Phase 2-specific: check top-level structures
        assert "phaseSummary" in result
        assert "interestStructures" in result
        assert isinstance(result["interestStructures"], list)
        assert "classPositions" in result
        assert isinstance(result["classPositions"], list)
