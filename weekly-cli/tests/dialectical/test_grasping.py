"""Test Phase 1: Phenomenon Grasping."""
import pytest
from unittest.mock import MagicMock
from dialectical.grasping import grasp_phenomena, build_events_text


class TestBuildEventsText:
    def test_formats_events(self):
        events = [
            {"title": "事件A", "summary": "概述A"},
            {"title": "事件B", "summary": "概述B"},
        ]
        text = build_events_text(events)
        assert "事件A" in text
        assert "事件B" in text
        assert "概述A" in text

    def test_handles_empty_list(self):
        text = build_events_text([])
        assert text == ""

    def test_truncates_long_summaries(self):
        events = [
            {"title": "Event", "summary": "X" * 300},
        ]
        text = build_events_text(events)
        assert "Event" in text
        # Summary should be truncated to 200 chars
        assert len(text.split("\n")[1].strip()) <= 200

    def test_handles_missing_summary(self):
        events = [
            {"title": "OnlyTitle"},
        ]
        text = build_events_text(events)
        assert "OnlyTitle" in text

    def test_handles_none_summary(self):
        events = [
            {"title": "Title", "summary": None},
        ]
        text = build_events_text(events)
        assert "Title" in text


class TestGraspPhenomena:
    def test_empty_events_returns_default(self):
        result = grasp_phenomena(client=None, events=[])
        assert result == {
            "selectedEvents": [],
            "excludedEvents": [],
            "sourceQualityReport": "无事件可供分析",
        }

    def test_defaults_applied_to_selected_events(self):
        """Test that id and sourceGrade defaults are applied when LLM omits them."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "selectedEvents": [
                {"title": "Event A", "summary": "Overview A"},  # no id, no sourceGrade
                {"title": "Event B", "summary": "Overview B", "id": "custom-id", "sourceGrade": {"reliability": "A", "credibility": 1, "rationale": "test"}},
            ],
            "excludedEvents": [],
            "sourceQualityReport": "ok",
        }
        result = grasp_phenomena(mock_client, [{"title": "Event A", "summary": "Overview A"}])
        assert len(result["selectedEvents"]) == 2
        # First event: defaults applied
        assert result["selectedEvents"][0]["id"] == "evt-1"
        assert result["selectedEvents"][0]["sourceGrade"]["reliability"] == "C"
        # Second event: original values preserved
        assert result["selectedEvents"][1]["id"] == "custom-id"
        assert result["selectedEvents"][1]["sourceGrade"]["reliability"] == "A"

    def test_selected_events_none_returns_empty(self):
        """Test that None selectedEvents is replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "selectedEvents": None,
            "excludedEvents": [],
            "sourceQualityReport": "ok",
        }
        result = grasp_phenomena(mock_client, [{"title": "T", "summary": "S"}])
        assert result["selectedEvents"] == []

    def test_selected_events_not_list_returns_empty(self):
        """Test that non-list selectedEvents is replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "selectedEvents": "error message",
            "excludedEvents": [],
            "sourceQualityReport": "ok",
        }
        result = grasp_phenomena(mock_client, [{"title": "T", "summary": "S"}])
        assert result["selectedEvents"] == []

    @pytest.mark.integration
    def test_grasp_phenomena_with_client(self):
        """Integration test: requires DEEPSEEK_API_KEY."""
        import os
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key or "dummy" in api_key.lower() or "pytest" in api_key.lower():
            pytest.skip("DEEPSEEK_API_KEY not set or is a dummy key")
        from chinese_scraper_utils import DeepSeekClient
        from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL_DIALECTICAL

        client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_DIALECTICAL, thinking=True)
        events = [
            {"title": "AI大模型价格战", "summary": "多家科技巨头宣布大幅下调大模型API价格"},
            {"title": "某明星演唱会", "summary": "某歌手巡回演唱会门票售罄"},
        ]
        result = grasp_phenomena(client, events)
        assert "selectedEvents" in result
        assert "excludedEvents" in result
        assert isinstance(result["selectedEvents"], list)
        # Verify structural validity: every selected event has required fields
        for e in result["selectedEvents"]:
            assert "id" in e
            assert "title" in e
            assert "sourceGrade" in e
