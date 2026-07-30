"""Test Phase 4: Historical Positioning — historical materialism positioning and cross-event synthesis."""
import pytest
from unittest.mock import MagicMock

from dialectical.positioning import build_positioning_context, position_historically


class TestBuildPositioningContext:
    def test_formats_events_with_all_fields(self):
        events = [
            {
                "id": "evt-1",
                "title": "测试事件",
                "materialContent": "测试物质内容",
                "summary": "测试概述",
            }
        ]
        ctx = build_positioning_context(events)
        assert "evt-1" in ctx
        assert "测试事件" in ctx
        assert "测试物质内容" in ctx
        assert "测试概述" in ctx

    def test_handles_empty_list(self):
        ctx = build_positioning_context([])
        assert ctx == ""

    def test_handles_missing_fields(self):
        events = [{"id": "evt-1"}]  # no title, summary, materialContent
        ctx = build_positioning_context(events)
        assert "evt-1" in ctx
        assert "(无标题)" in ctx

    def test_handles_none_summary_and_material(self):
        events = [
            {"id": "evt-1", "title": "Title", "summary": None, "materialContent": None}
        ]
        ctx = build_positioning_context(events)
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
        ctx = build_positioning_context(events)
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
        ctx = build_positioning_context(events)
        assert "事件A" in ctx
        assert "事件B" in ctx
        assert "[事件 1]" in ctx
        assert "[事件 2]" in ctx

    def test_includes_impact_and_infogain_scores(self):
        events = [
            {
                "id": "evt-1",
                "title": "事件A",
                "summary": "概述A",
                "impactScore": 5,
                "infoGainScore": 4,
            }
        ]
        ctx = build_positioning_context(events)
        assert "5" in ctx
        assert "4" in ctx

    def test_handles_scores_none(self):
        events = [
            {
                "id": "evt-1",
                "title": "事件A",
                "summary": "概述A",
                "impactScore": None,
                "infoGainScore": None,
            }
        ]
        ctx = build_positioning_context(events)
        # Should not crash, score lines should not appear
        assert "None" not in ctx


class TestPositionHistorically:
    def test_empty_events_returns_default(self):
        result = position_historically(client=None, events=[])
        assert result == {
            "phaseSummary": "无事件可供历史定位",
            "events": [],
            "crossCuttingSynthesis": "",
            "epochThemes": [],
            "systemArchetypes": [],
            "hiddenConnections": [],
            "historicalAnalogies": [],
        }

    def test_none_events_returns_empty_list(self):
        """Test that None events is replaced with empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": None,
        }
        result = position_historically(
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
        result = position_historically(
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
        result = position_historically(
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
            "crossCuttingSynthesis": None,
            "epochThemes": None,
            "systemArchetypes": None,
            "hiddenConnections": None,
            "historicalAnalogies": None,
        }
        result = position_historically(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert result["crossCuttingSynthesis"] == ""
        assert result["epochThemes"] == []
        assert result["systemArchetypes"] == []
        assert result["hiddenConnections"] == []
        assert result["historicalAnalogies"] == []

    def test_non_list_cross_fields_defaulted(self):
        """Test that non-list cross-event fields get empty list."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
            "epochThemes": "not a list",
            "systemArchetypes": 123,
            "hiddenConnections": None,
            "historicalAnalogies": {},
        }
        result = position_historically(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert result["epochThemes"] == []
        assert result["systemArchetypes"] == []
        assert result["hiddenConnections"] == []
        assert result["historicalAnalogies"] == []

    def test_calls_chat_json_with_correct_prompt(self):
        """Test that the LLM is called with formatted positioning prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
            "crossCuttingSynthesis": "",
            "epochThemes": [],
            "systemArchetypes": [],
            "hiddenConnections": [],
            "historicalAnalogies": [],
        }
        events = [
            {
                "id": "evt-1",
                "title": "AI大模型价格战",
                "materialContent": "科技资本通过价格战清洗中小竞争者",
                "summary": "多家科技巨头宣布大幅下调大模型API价格",
            }
        ]
        position_historically(mock_client, events)

        # Verify chat_json was called
        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]  # messages
        user_content = call_args[1]["content"]
        assert "AI大模型价格战" in user_content
        assert "科技资本通过价格战清洗中小竞争者" in user_content

    def test_per_event_analysis_defaults(self):
        """Test that per-event historical positioning fields default to empty string."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [
                {"id": "evt-1", "title": "T", "summary": "S"},
                {
                    "id": "evt-2",
                    "title": "T2",
                    "summary": "S2",
                    "productiveForces": "生产力分析",
                    "productionRelations": "生产关系分析",
                    "baseStructure": "经济基础分析",
                    "superstructure": "上层建筑分析",
                    "classForceComparison": "阶级力量对比分析",
                    "historicalPosition": "历史方位分析",
                },
            ],
        }
        result = position_historically(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        events = result["events"]
        assert len(events) == 2
        # First event: defaults applied
        assert events[0]["productiveForces"] == ""
        assert events[0]["productionRelations"] == ""
        assert events[0]["baseStructure"] == ""
        assert events[0]["superstructure"] == ""
        assert events[0]["classForceComparison"] == ""
        assert events[0]["historicalPosition"] == ""
        # Second event: original values preserved
        assert events[1]["productiveForces"] == "生产力分析"
        assert events[1]["productionRelations"] == "生产关系分析"
        assert events[1]["baseStructure"] == "经济基础分析"
        assert events[1]["superstructure"] == "上层建筑分析"
        assert events[1]["classForceComparison"] == "阶级力量对比分析"
        assert events[1]["historicalPosition"] == "历史方位分析"

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
        result = position_historically(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert len(result["events"]) == 1
        assert result["events"][0]["title"] == "Valid"

    def test_includes_phase_summary_in_result(self):
        """Test that phaseSummary is passed through from LLM response."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "本周历史定位集中在科技资本与监管的博弈",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
        }
        result = position_historically(
            mock_client, [{"id": "evt-1", "title": "T", "summary": "S"}]
        )
        assert "本周历史定位集中在科技资本与监管的博弈" in result["phaseSummary"]

    @pytest.mark.integration
    def test_position_historically_integration(self):
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
                "materialContent": "科技资本通过价格战清洗中小竞争者，头部企业抢占市场份额",
                "summary": "多家科技巨头宣布大幅下调大模型API价格",
            }
        ]
        result = position_historically(client, events)
        assert "events" in result
        assert len(result["events"]) >= 1
        e = result["events"][0]
        assert "id" in e
        assert "title" in e
        assert "summary" in e
        # Phase 4-specific: check per-event historical materialism fields
        assert "productiveForces" in e
        assert "productionRelations" in e
        assert "baseStructure" in e
        assert "superstructure" in e
        assert "classForceComparison" in e
        assert "historicalPosition" in e
        # Check cross-event synthesis fields
        assert "phaseSummary" in result
        assert "crossCuttingSynthesis" in result
        assert isinstance(result["crossCuttingSynthesis"], str)
        assert "epochThemes" in result
        assert isinstance(result["epochThemes"], list)
        assert "systemArchetypes" in result
        assert isinstance(result["systemArchetypes"], list)
        assert "hiddenConnections" in result
        assert isinstance(result["hiddenConnections"], list)
        assert "historicalAnalogies" in result
        assert isinstance(result["historicalAnalogies"], list)
