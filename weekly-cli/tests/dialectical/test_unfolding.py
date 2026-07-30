"""Test Phase 3: Dialectical Unfolding — the three-law dialectical analysis."""
import json
import pytest
from unittest.mock import MagicMock

from dialectical.unfolding import build_search_context, build_events_text, unfold_dialectics


class TestBuildSearchContext:
    def test_formats_search_results(self):
        results = [
            {
                "title": "搜索结果标题A",
                "url": "https://example.com/a",
                "snippet": "这是搜索结果的摘要A",
            },
            {
                "title": "搜索结果标题B",
                "url": "https://example.com/b",
                "snippet": "这是搜索结果的摘要B",
            },
        ]
        ctx = build_search_context(results)
        assert "搜索结果标题A" in ctx
        assert "https://example.com/a" in ctx
        assert "摘要A" in ctx
        assert "搜索结果标题B" in ctx
        assert "https://example.com/b" in ctx
        assert "摘要B" in ctx
        assert "<result_1>" in ctx
        assert "</result_2>" in ctx

    def test_handles_empty_list(self):
        ctx = build_search_context([])
        assert "无搜索结果" in ctx or "information" in ctx.lower()

    def test_sanitizes_control_characters(self):
        results = [
            {
                "title": "标题\x00带控制字符",
                "url": "https://example.com",
                "snippet": "摘要\x1F也有控制字符",
            }
        ]
        ctx = build_search_context(results)
        assert "\x00" not in ctx
        assert "\x1F" not in ctx

    def test_truncates_long_fields(self):
        results = [
            {
                "title": "A" * 1000,
                "url": "https://example.com/" + "x" * 1000,
                "snippet": "B" * 1000,
            }
        ]
        ctx = build_search_context(results)
        # Should not contain the full 1000-char strings
        assert len(ctx) < 3000  # truncated significantly


class TestBuildEventsText:
    def test_formats_event_with_search_results(self):
        event = {
            "id": "evt-1",
            "title": "测试事件",
            "summary": "这是一个测试事件概述",
            "impactScore": 4,
            "infoGainScore": 3,
        }
        search_results = [
            {
                "title": "相关报道",
                "url": "https://example.com/1",
                "snippet": "报道内容",
            }
        ]
        text = build_events_text(event, search_results)
        assert "测试事件" in text
        assert "测试事件概述" in text
        assert "相关报道" in text
        assert "https://example.com/1" in text

    def test_handles_missing_summary(self):
        event = {"id": "evt-1", "title": "无概述事件"}
        text = build_events_text(event, [])
        assert "无概述事件" in text
        assert "无概述" in text or "(无概述)" in text

    def test_handles_empty_search_results(self):
        event = {"id": "evt-1", "title": "Event", "summary": "Summary"}
        text = build_events_text(event, [])
        assert "Event" in text
        assert "无搜索结果" in text

    def test_includes_material_content_when_present(self):
        event = {
            "id": "evt-1",
            "title": "Event",
            "summary": "Summary",
            "materialContent": "物质内容",
        }
        text = build_events_text(event, [])
        assert "物质内容" in text

    def test_sanitizes_control_characters_in_event(self):
        event = {
            "title": "带\x00控制\x08字符的标题",
            "summary": "概述\x1F含控制字符",
        }
        text = build_events_text(event, [])
        assert "\x00" not in text
        assert "\x08" not in text
        assert "\x1F" not in text

    def test_includes_impact_and_infogain_scores(self):
        event = {
            "id": "evt-1",
            "title": "Event",
            "summary": "Summary",
            "impactScore": 5,
            "infoGainScore": 4,
        }
        text = build_events_text(event, [])
        assert "5" in text
        assert "4" in text


class TestUnfoldDialectics:
    def test_empty_event_returns_default(self):
        """Test that None client with empty event returns a minimal default."""
        result = unfold_dialectics(
            client=None,
            event={"title": "Empty", "summary": ""},
            search_results=[],
        )
        assert "unityOfOpposites" in result
        assert "quantityQuality" in result
        assert "negationOfNegation" in result

    def test_calls_chat_json_with_correct_prompt(self):
        """Test that the LLM is called with formatted unfolding prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "辩证展开总述",
            "events": [{"id": "evt-1", "title": "测试事件", "summary": "概述"}],
            "dialecticalConfidence": "MEDIUM",
            "unityOfOpposites": {
                "identity": "同一性分析",
                "struggle": "斗争性分析",
                "particularity": "特殊性分析",
                "universality": "普遍性分析",
            },
            "quantityQuality": {
                "currentPhase": "量变积累",
                "quantitativeDirection": "上升趋势",
                "measure": "度量关节线",
                "newQuality": "新质量特征",
                "oldQualityNegated": "旧质量内容",
            },
            "negationOfNegation": {
                "oldThing": "旧事物",
                "firstNegation": "第一次否定",
                "internalNegation": "内部否定",
                "direction": "螺旋上升",
                "stageCharacteristics": "当前阶段特征",
            },
            "adversarialReview": {
                "reviewAspect": "审查方面",
                "originalClaim": "原始论断",
                "critique": "批判审查",
                "revisedClaim": "修正论断",
                "confidence": "MEDIUM",
            },
            "causalLoopDiagram": {
                "diagramId": "cld-001",
                "description": "描述",
                "nodes": [],
                "positiveFeedbackLoops": [],
                "negativeFeedbackLoops": [],
                "keyLeveragePoints": [],
            },
            "dataValidation": {
                "validationCheck": "验证项",
                "dataSource": "数据来源",
                "result": "结果",
                "issues": [],
                "confidence": "HIGH",
            },
        }
        event = {
            "id": "evt-1",
            "title": "AI大模型价格战",
            "summary": "多家科技巨头宣布大幅下调大模型API价格",
        }
        search_results = [
            {
                "title": "相关报道",
                "url": "https://example.com/1",
                "snippet": "报道内容摘要",
            }
        ]
        result = unfold_dialectics(mock_client, event, search_results, idx=1)

        # Verify chat_json was called
        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]  # messages
        user_content = call_args[1]["content"]
        assert "AI大模型价格战" in user_content
        assert "多家科技巨头" in user_content
        assert "https://example.com/1" in user_content

        # Verify result structure
        assert "unityOfOpposites" in result
        assert "quantityQuality" in result
        assert "negationOfNegation" in result
        assert result["unityOfOpposites"]["identity"] == "同一性分析"
        assert result["quantityQuality"]["currentPhase"] == "量变积累"
        assert result["negationOfNegation"]["direction"] == "螺旋上升"

    def test_defaults_applied_to_missing_top_level_fields(self):
        """Test that missing top-level fields get defaults."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
            "dialecticalConfidence": "LOW",
            # unityOfOpposites, quantityQuality, negationOfNegation missing
        }
        result = unfold_dialectics(
            mock_client, {"title": "T", "summary": "S"}, []
        )
        assert "unityOfOpposites" in result
        assert "quantityQuality" in result
        assert "negationOfNegation" in result
        assert "identity" in result["unityOfOpposites"]
        assert "currentPhase" in result["quantityQuality"]
        assert "direction" in result["negationOfNegation"]
        assert result["dialecticalConfidence"] == "LOW"

    def test_none_top_level_fields_defaulted(self):
        """Test that None top-level fields get default values."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
            "dialecticalConfidence": "MEDIUM",
            "unityOfOpposites": None,
            "quantityQuality": None,
            "negationOfNegation": None,
            "adversarialReview": None,
            "causalLoopDiagram": None,
            "dataValidation": None,
        }
        result = unfold_dialectics(
            mock_client, {"title": "T", "summary": "S"}, []
        )
        assert isinstance(result["unityOfOpposites"], dict)
        assert isinstance(result["quantityQuality"], dict)
        assert isinstance(result["negationOfNegation"], dict)
        assert isinstance(result["adversarialReview"], dict)
        assert isinstance(result["causalLoopDiagram"], dict)
        assert isinstance(result["dataValidation"], dict)

    def test_includes_search_context_in_prompt(self):
        """Test that search results appear in the prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "phaseSummary": "test",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
            "dialecticalConfidence": "MEDIUM",
            "unityOfOpposites": {"identity": "id", "struggle": "s", "particularity": "p", "universality": "u"},
            "quantityQuality": {
                "currentPhase": "量变积累",
                "quantitativeDirection": "d",
                "measure": "m",
                "newQuality": "nq",
                "oldQualityNegated": "oq",
            },
            "negationOfNegation": {
                "oldThing": "o", "firstNegation": "f", "internalNegation": "i",
                "direction": "螺旋上升", "stageCharacteristics": "s",
            },
        }
        search_results = [
            {"title": "Bing结果", "url": "https://bing.com", "snippet": "Bing摘要"},
            {"title": "DDG结果", "url": "https://duckduckgo.com", "snippet": "DDG摘要"},
        ]
        unfold_dialectics(
            mock_client, {"title": "T", "summary": "S"}, search_results
        )
        user_content = mock_client.chat_json.call_args[0][0][1]["content"]
        assert "Bing结果" in user_content
        assert "DDG结果" in user_content

    @pytest.mark.integration
    def test_unfold_dialectics_integration(self):
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
        event = {
            "id": "evt-1",
            "title": "AI大模型价格战全面爆发",
            "materialContent": "科技资本通过价格战清洗中小竞争者",
            "summary": "多家科技巨头宣布大幅下调大模型API价格，引发行业震动",
        }
        search_results = [
            {
                "title": "AI价格战：巨头争相降价",
                "url": "https://example.com/1",
                "snippet": "多家企业下调API价格",
            }
        ]
        result = unfold_dialectics(client, event, search_results, idx=1)
        # Verify core dialectical structures
        assert "unityOfOpposites" in result
        uoo = result["unityOfOpposites"]
        assert isinstance(uoo, dict)
        assert "identity" in uoo, f"Missing identity in unityOfOpposites: {list(uoo.keys())}"
        assert "struggle" in uoo

        assert "quantityQuality" in result
        qq = result["quantityQuality"]
        assert isinstance(qq, dict)
        assert "currentPhase" in qq, f"Missing currentPhase in quantityQuality: {list(qq.keys())}"
        valid_phases = {"量变积累", "质的飞跃", "量变中的局部质变"}
        assert qq["currentPhase"] in valid_phases, f"Unexpected phase: {qq['currentPhase']}"

        assert "negationOfNegation" in result
        non = result["negationOfNegation"]
        assert isinstance(non, dict)
        assert "direction" in non, f"Missing direction in negationOfNegation: {list(non.keys())}"
        valid_directions = {"螺旋上升", "暂时倒退", "停滞"}
        assert non["direction"] in valid_directions, f"Unexpected direction: {non['direction']}"

        assert "dialecticalConfidence" in result
        valid_confidence = {"HIGH", "MEDIUM", "LOW"}
        assert result["dialecticalConfidence"] in valid_confidence

        # Verify events array
        assert "events" in result
        assert isinstance(result["events"], list)
        assert len(result["events"]) >= 1
