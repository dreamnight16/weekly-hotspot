"""Test dual-layer merge logic."""
import pytest
from schema import (
    PhenomenonGrasping, SelectedEvent, ExcludedEvent,
    SourceGrade, GDELTBaseline,
)


class TestMerge:
    def test_merge_with_empirical_verified(self):
        from merger import merge_phase
        dialectical = PhenomenonGrasping(
            phaseSummary="辩证总结",
            selectedEvents=[
                SelectedEvent(
                    id="evt-1", title="测试", summary="概述",
                    materialContent="有物质内容",
                    isDirectExpression=True,
                    sourceGrade=SourceGrade(
                        reliability="A", credibility=2, rationale="官方"
                    )
                )
            ],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="好"
        )
        empirical = {"verificationNote": "来源质量确认", "verified": True}
        result = merge_phase(dialectical, empirical)
        assert result["empiricalVerified"] is True
        assert result["empiricalDegraded"] is False

    def test_merge_empirical_degraded(self):
        from merger import merge_phase
        dialectical = PhenomenonGrasping(
            phaseSummary="辩证总结",
            selectedEvents=[],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="一般"
        )
        result = merge_phase(dialectical, None)
        assert result["empiricalDegraded"] is True
        assert result["empiricalVerified"] is False

    def test_merge_preserves_dialectical_data(self):
        from merger import merge_phase
        dialectical = PhenomenonGrasping(
            phaseSummary="辩证总结",
            selectedEvents=[
                SelectedEvent(
                    id="evt-1", title="测试", summary="概述",
                    materialContent="物质内容",
                    isDirectExpression=True,
                    sourceGrade=SourceGrade(
                        reliability="B", credibility=3, rationale="待确认"
                    )
                )
            ],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="一般"
        )
        result = merge_phase(dialectical, None)
        assert result["phaseSummary"] == "辩证总结"
        assert len(result["selectedEvents"]) == 1
