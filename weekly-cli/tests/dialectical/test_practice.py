"""Test Phase 5: Practice Orientation — judgment, scenarios, signals, and calibration."""
import pytest
from unittest.mock import MagicMock

from dialectical.practice import build_practice_context, orient_practice


class TestBuildPracticeContext:
    def test_formats_events_with_all_fields(self):
        positioning_result = {
            "phaseSummary": "测试历史定位摘要",
            "events": [
                {
                    "id": "evt-1",
                    "title": "AI大模型价格战",
                    "summary": "多家科技巨头宣布大幅下调大模型API价格",
                    "materialContent": "科技资本通过价格战清洗中小竞争者",
                    "impactScore": 5,
                    "infoGainScore": 4,
                    "productiveForces": "科技生产力快速发展",
                    "productionRelations": "数据垄断与开源社区博弈",
                }
            ],
        }
        ctx = build_practice_context(positioning_result)
        assert "evt-1" in ctx
        assert "AI大模型价格战" in ctx
        assert "多家科技巨头宣布大幅下调大模型API价格" in ctx
        assert "科技资本通过价格战清洗中小竞争者" in ctx
        assert "生产力" in ctx
        assert "数据垄断" in ctx

    def test_handles_empty_events(self):
        ctx = build_practice_context({"events": []})
        assert ctx == ""

    def test_handles_empty_positioning_result(self):
        ctx = build_practice_context({})
        assert ctx == ""

    def test_handles_none_events(self):
        ctx = build_practice_context({"events": None})
        assert ctx == ""

    def test_handles_missing_optional_fields(self):
        """Fields like summary, materialContent, impactScore may be missing."""
        positioning_result = {
            "events": [
                {"id": "evt-1", "title": "事件A"}
            ]
        }
        ctx = build_practice_context(positioning_result)
        assert "evt-1" in ctx
        assert "事件A" in ctx

    def test_includes_positioning_analysis_fields(self):
        positioning_result = {
            "events": [
                {
                    "id": "evt-1",
                    "title": "事件A",
                    "summary": "概述",
                    "historicalPosition": "历史转折点",
                    "classForceComparison": "中产阶级力量增强",
                }
            ]
        }
        ctx = build_practice_context(positioning_result)
        assert "历史转折点" in ctx
        assert "中产阶级力量增强" in ctx

    def test_truncates_long_summary(self):
        positioning_result = {
            "events": [
                {
                    "id": "evt-1",
                    "title": "Event",
                    "summary": "S" * 500,
                }
            ]
        }
        ctx = build_practice_context(positioning_result)
        assert len(ctx) > 0
        # Summary truncated to 300 chars
        summary_line = [l for l in ctx.split("\n") if "概述" in l]
        if summary_line:
            assert len(summary_line[0].strip()) <= 300 + len("  概述: ")

    def test_truncates_long_material_content(self):
        positioning_result = {
            "events": [
                {
                    "id": "evt-1",
                    "title": "Event",
                    "summary": "概述",
                    "materialContent": "M" * 600,
                }
            ]
        }
        ctx = build_practice_context(positioning_result)
        material_line = [l for l in ctx.split("\n") if "物质内容" in l]
        if material_line:
            assert len(material_line[0].strip()) <= 500 + len("  物质内容: ")

    def test_includes_historical_position_summary(self):
        """The context should include the phaseSummary from positioning."""
        positioning_result = {
            "phaseSummary": "本周科技领域呈现加速分化态势",
            "events": [
                {"id": "evt-1", "title": "事件A", "summary": "概述"}
            ]
        }
        ctx = build_practice_context(positioning_result)
        assert "本周科技领域呈现加速分化态势" in ctx

    def test_handles_none_scores(self):
        positioning_result = {
            "events": [
                {
                    "id": "evt-1",
                    "title": "事件A",
                    "summary": "概述",
                    "impactScore": None,
                    "infoGainScore": None,
                }
            ]
        }
        ctx = build_practice_context(positioning_result)
        assert "None" not in ctx

    def test_multiple_events(self):
        positioning_result = {
            "events": [
                {"id": "evt-1", "title": "事件A", "summary": "概述A"},
                {"id": "evt-2", "title": "事件B", "summary": "概述B"},
            ]
        }
        ctx = build_practice_context(positioning_result)
        assert "[事件 1]" in ctx
        assert "[事件 2]" in ctx
        assert "事件A" in ctx
        assert "事件B" in ctx


class TestOrientPractice:
    def test_empty_events_returns_default(self):
        result = orient_practice(client=None, positioning_result={"events": []})
        assert result["overallJudgment"] == "无事件可供实践导向分析"
        assert result["scenarios"] == []
        assert result["practiceSignificance"] == ""
        assert result["signalsToWatch"] == []
        assert "lastWeekCalibration" in result

    def test_none_events_returns_default(self):
        result = orient_practice(client=None, positioning_result={"events": None})
        assert result["overallJudgment"] == "无事件可供实践导向分析"

    def test_empty_positioning_result_returns_default(self):
        result = orient_practice(client=None, positioning_result={})
        assert result["overallJudgment"] == "无事件可供实践导向分析"

    def test_none_scenarios_defaulted(self):
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": None,
            "practiceSignificance": "test significance",
            "signalsToWatch": [],
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert result["scenarios"] == []

    def test_non_list_scenarios_defaulted(self):
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": "not a list",
            "practiceSignificance": "test",
            "signalsToWatch": [],
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert result["scenarios"] == []

    def test_none_signals_defaulted(self):
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": [],
            "practiceSignificance": "test",
            "signalsToWatch": None,
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert result["signalsToWatch"] == []

    def test_non_list_signals_defaulted(self):
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": [],
            "practiceSignificance": "test",
            "signalsToWatch": "not a list",
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert result["signalsToWatch"] == []

    def test_none_overall_judgment_defaulted(self):
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": None,
            "scenarios": [],
            "practiceSignificance": "test",
            "signalsToWatch": [],
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert result["overallJudgment"] == ""

    def test_none_practice_significance_defaulted(self):
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": [],
            "practiceSignificance": None,
            "signalsToWatch": [],
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert result["practiceSignificance"] == ""

    def test_scenario_defaults_applied(self):
        """Test that per-scenario fields are defaulted."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": [
                {
                    "scenarioId": "sc-1",
                    "title": "基线情景",
                    "description": "持续发展",
                    "scenarioType": "baseline",
                    "probability": 0.5,
                    "keyAssumptions": None,
                    "earlySignals": ["信号"],
                    "relatedEventIds": ["evt-1"],
                }
            ],
            "practiceSignificance": "test",
            "signalsToWatch": [],
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert result["scenarios"][0]["keyAssumptions"] == []

    def test_signal_defaults_applied(self):
        """Test that per-signal fields are defaulted."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": [],
            "practiceSignificance": "test",
            "signalsToWatch": [
                {
                    "signalName": "政策变化",
                    "description": "描述",
                    "indicator": "指标",
                    "currentValue": "当前值",
                    "threshold": "阈值",
                    "trend": "上升",
                    "priority": None,
                }
            ],
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert result["signalsToWatch"][0]["priority"] == 3

    def test_last_week_calibration_defaults(self):
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": [],
            "practiceSignificance": "test",
            "signalsToWatch": [],
            "lastWeekCalibration": None,
        }
        result = orient_practice(
            mock_client,
            {"events": [{"id": "evt-1", "title": "T", "summary": "S"}]},
        )
        assert isinstance(result["lastWeekCalibration"], dict)
        assert result["lastWeekCalibration"].get("predictionSummary") == ""
        assert result["lastWeekCalibration"].get("actualOutcome") == ""
        assert result["lastWeekCalibration"].get("calibrationNote") == ""
        assert result["lastWeekCalibration"].get("accuracyScore") is None

    def test_calls_chat_json_with_correct_content(self):
        """Test that the LLM is called with formatted practice prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "测试总体判断",
            "scenarios": [
                {
                    "scenarioId": "sc-1",
                    "title": "基线情景",
                    "description": "情景描述",
                    "scenarioType": "baseline",
                    "probability": 0.5,
                    "keyAssumptions": ["假设A"],
                    "earlySignals": ["信号A"],
                    "relatedEventIds": ["evt-1"],
                }
            ],
            "practiceSignificance": "测试实践意义",
            "signalsToWatch": [
                {
                    "signalName": "政策变量",
                    "description": "需要关注政策动向",
                    "indicator": "新政策发布频率",
                    "currentValue": "每月一次",
                    "threshold": "每周一次",
                    "trend": "上升",
                    "priority": 2,
                }
            ],
            "lastWeekCalibration": {
                "predictionSummary": "上周预测摘要",
                "actualOutcome": "实际结果",
                "calibrationNote": "校准说明",
                "accuracyScore": 0.7,
            },
        }
        positioning_result = {
            "phaseSummary": "本周科技领域加速分化",
            "events": [
                {
                    "id": "evt-1",
                    "title": "AI大模型价格战",
                    "materialContent": "科技资本通过价格战清洗中小竞争者",
                    "summary": "多家科技巨头宣布大幅下调大模型API价格",
                    "productiveForces": "科技生产力快速发展",
                }
            ],
        }
        orient_practice(mock_client, positioning_result)

        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]
        user_content = call_args[1]["content"]
        assert "AI大模型价格战" in user_content
        assert "科技资本通过价格战清洗中小竞争者" in user_content
        assert "本周科技领域加速分化" in user_content
        assert "实践导向" in user_content or "总体判断" in user_content

    def test_includes_phase_summary_context(self):
        """The phase summary from positioning should appear in the prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": [],
            "practiceSignificance": "test",
            "signalsToWatch": [],
            "lastWeekCalibration": {},
        }
        positioning_result = {
            "phaseSummary": "历史定位：科技资本与公共权力的结构性博弈",
            "events": [{"id": "evt-1", "title": "T", "summary": "S"}],
        }
        orient_practice(mock_client, positioning_result)
        call_args = mock_client.chat_json.call_args[0][0]
        user_content = call_args[1]["content"]
        assert "历史定位：科技资本与公共权力的结构性博弈" in user_content

    def test_non_dict_events_in_positioning_skipped(self):
        """Non-dict entries in positioning_result events list are handled gracefully."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "overallJudgment": "test",
            "scenarios": [],
            "practiceSignificance": "test",
            "signalsToWatch": [],
            "lastWeekCalibration": {},
        }
        result = orient_practice(
            mock_client,
            {"events": ["not a dict", 123]},
        )
        assert result["overallJudgment"] == "无事件可供实践导向分析"

    @pytest.mark.integration
    def test_orient_practice_integration(self):
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
        positioning_result = {
            "phaseSummary": (
                "本周热点事件呈现技术资本扩张与公共权力制衡的结构性矛盾，"
                "AI产业处于生产力超前发展与生产关系滞后调整的历史方位。"
            ),
            "events": [
                {
                    "id": "evt-1",
                    "title": "AI大模型价格战全面爆发",
                    "materialContent": "科技资本通过价格战清洗中小竞争者，头部企业抢占市场份额",
                    "summary": "多家科技巨头宣布大幅下调大模型API价格",
                    "productiveForces": "大规模算力基础设施和算法优化使边际成本大幅下降",
                    "productionRelations": "数据垄断和开源模式的博弈加剧",
                    "baseStructure": "科技金融资本支撑的规模经济效应",
                    "superstructure": "监管政策滞后于技术发展速度",
                    "classForceComparison": "头部科技企业强势、中小企业受压、消费者短期受益",
                    "historicalPosition": "AI产业化从探索期进入规模化竞争期的转折点",
                }
            ],
        }
        result = orient_practice(client, positioning_result)
        assert "overallJudgment" in result
        assert isinstance(result["overallJudgment"], str)
        assert len(result["overallJudgment"]) > 0
        assert "scenarios" in result
        assert isinstance(result["scenarios"], list)
        assert len(result["scenarios"]) >= 1
        # Check scenario structure
        sc = result["scenarios"][0]
        assert "scenarioId" in sc
        assert "title" in sc
        assert "description" in sc
        assert "scenarioType" in sc
        assert sc["scenarioType"] in ("baseline", "alternative", "wildcard")
        assert "probability" in sc
        assert isinstance(sc["probability"], (int, float))
        assert "practiceSignificance" in result
        assert isinstance(result["practiceSignificance"], str)
        assert len(result["practiceSignificance"]) > 0
        assert "signalsToWatch" in result
        assert isinstance(result["signalsToWatch"], list)
        if result["signalsToWatch"]:
            sig = result["signalsToWatch"][0]
            assert "signalName" in sig
            assert "indicator" in sig
            assert "priority" in sig
        assert "lastWeekCalibration" in result
        assert isinstance(result["lastWeekCalibration"], dict)
