"""Test Pydantic v2 schema models for 格物 v2."""
import json
import pytest
from schema import (
    SourceGrade, GDELTBaseline, SelectedEvent, ExcludedEvent,
    InterestStructure, ClassPosition, NineDimScores, CompetingHypothesis,
    UnityOfOpposites, QuantityQuality, NegationOfNegation,
    AdversarialReview, CausalLoopDiagram, DataValidation,
    EpochTheme, SystemArchetype, HiddenConnection, HistoricalAnalogy,
    Scenario, WatchSignal, LastWeekCalibration,
    EvidenceTrace, TracedClaim, TracedSource, IssueMetadata,
    PhenomenonGrasping, ContradictionIdentification,
    DialecticalUnfolding, HistoricalPositioning, PracticeOrientation,
    WeeklyIssue, RawEvent, CensoredEvent,
)


class TestSourceGrade:
    def test_valid_source_grade(self):
        sg = SourceGrade(reliability="A", credibility=1, rationale="官方发布")
        assert sg.reliability == "A"
        assert sg.credibility == 1

    def test_invalid_reliability_defaults(self):
        sg = SourceGrade(reliability="X", credibility=3, rationale="test")
        assert sg.reliability in ("A", "B", "C", "D", "E", "F")  # sanitized

    def test_credibility_clamped(self):
        sg = SourceGrade(reliability="B", credibility=99, rationale="test")
        assert 1 <= sg.credibility <= 6


class TestSelectedEvent:
    def test_valid_event(self):
        e = SelectedEvent(
            id="evt-1", title="测试事件", summary="概述",
            sourceUrl=None, materialContent="有物质利益关系",
            isDirectExpression=True,
            sourceGrade=SourceGrade(reliability="A", credibility=2, rationale="官方")
        )
        assert e.id == "evt-1"
        assert e.isDirectExpression is True


class TestNineDimScores:
    def test_all_dimensions(self):
        s = NineDimScores(
            magnitude=(5, 0.9), scope=(3, 0.8), velocity=(2, 0.7),
            novelty=(4, 0.6), cascadePotential=(3, 0.5),
            actorProminence=(4, 0.9), uncertainty=(2, 0.8),
            polarity=(4, 0.7), durability=(3, 0.6)
        )
        assert s.magnitude[0] == 5
        assert s.cascadePotential[1] == 0.5

    def test_scores_clamped(self):
        s = NineDimScores(
            magnitude=(99, 9.9), scope=(0, -1.0), velocity=(2, 0.5),
            novelty=(3, 0.5), cascadePotential=(3, 0.5),
            actorProminence=(3, 0.5), uncertainty=(3, 0.5),
            polarity=(3, 0.5), durability=(3, 0.5)
        )
        assert 1 <= s.magnitude[0] <= 10
        assert 1 <= s.scope[0] <= 10
        assert 0.0 <= s.magnitude[1] <= 1.0


class TestDialecticalModels:
    def test_unity_of_opposites(self):
        u = UnityOfOpposites(
            identity="双方在政策框架下相互依存",
            struggle="平台通过抽成转嫁成本",
            particularity="不同于传统制造业劳资矛盾",
            universality="资本将外部成本内部化的普遍规律"
        )
        assert "相互依存" in u.identity

    def test_quantity_quality(self):
        q = QuantityQuality(
            currentPhase="量变积累",
            quantitativeDirection="平台抽成比例持续上升",
            measure="当抽成比例超过骑手承受阈值时发生质变",
            newQuality=None,
            oldQualityNegated="骑手作为独立承包商的旧形态"
        )
        assert q.currentPhase == "量变积累"

    def test_negation_of_negation(self):
        n = NegationOfNegation(
            oldThing="平台-骑手的旧雇佣关系",
            firstNegation="灵活用工模式否定固定雇佣",
            internalNegation="骑手集体权益意识生长",
            direction="螺旋上升",
            stageCharacteristics="否定之否定的初期阶段"
        )
        assert n.direction == "螺旋上升"


class TestPhaseModels:
    def test_phenomenon_grasping_minimal(self):
        pg = PhenomenonGrasping(
            phaseSummary="测试总结",
            selectedEvents=[],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="来源质量良好"
        )
        assert pg.phaseSummary == "测试总结"

    def test_contradiction_identification(self):
        ci = ContradictionIdentification(
            phaseSummary="总结",
            events=[],
            overallContradictionLandscape="整体格局"
        )
        assert ci.overallContradictionLandscape == "整体格局"

    def test_dialectical_unfolding(self):
        du = DialecticalUnfolding(
            phaseSummary="总结",
            events=[],
            dialecticalConfidence="HIGH"
        )
        assert du.dialecticalConfidence == "HIGH"

    def test_historical_positioning(self):
        hp = HistoricalPositioning(
            phaseSummary="总结",
            events=[],
            crossCuttingSynthesis=None,
            historicalAnalogies=[]
        )
        assert hp.phaseSummary == "总结"

    def test_practice_orientation(self):
        po = PracticeOrientation(
            overallJudgment="本周矛盾处于积累期",
            scenarios=[],
            practiceSignificance="有助于理解平台劳动关系",
            signalsToWatch=[],
            lastWeekCalibration=None
        )
        assert "积累期" in po.overallJudgment


class TestWeeklyIssue:
    def test_minimal_issue(self):
        wi = WeeklyIssue(
            id="2026-W31",
            weekStart="2026-07-27",
            weekEnd="2026-08-02",
            events=[],
            phase1=PhenomenonGrasping(
                phaseSummary="", selectedEvents=[],
                excludedEvents=[], gdeltBaseline=None,
                sourceQualityReport=""
            ),
            phase2=None,
            phase3=None,
            phase4=None,
            phase5=None,
            evidenceTrace=EvidenceTrace(claims=[], totalVerifiedClaims=0),
            metadata=IssueMetadata(
                modelVersions={}, verificationPasses=0,
                empiricalDegradations=[], totalApiCost=0.0,
                runDuration=0.0, runId="test"
            )
        )
        assert wi.id == "2026-W31"

    def test_issue_json_roundtrip(self):
        wi = WeeklyIssue(
            id="2026-W31", weekStart="2026-07-27", weekEnd="2026-08-02",
            events=[], phase1=PhenomenonGrasping(
                phaseSummary="t", selectedEvents=[], excludedEvents=[],
                gdeltBaseline=None, sourceQualityReport=""
            ),
            evidenceTrace=EvidenceTrace(claims=[], totalVerifiedClaims=0),
            metadata=IssueMetadata(
                modelVersions={}, verificationPasses=0,
                empiricalDegradations=[], totalApiCost=0.0,
                runDuration=0.0, runId="t"
            )
        )
        d = wi.model_dump_json(ensure_ascii=False)
        wi2 = WeeklyIssue.model_validate_json(d)
        assert wi2.id == wi.id


class TestEvidenceTrace:
    def test_traced_claim(self):
        tc = TracedClaim(
            claimId="c-1", claim="测试断言", phase="phase2",
            confidence="HIGH",
            sources=[TracedSource(
                sourceName="新华社", sourceUrl="https://example.com",
                reliability="A", credibility=2
            )],
            independentCorroborations=2,
            verificationMethod="交叉验证"
        )
        assert tc.confidence == "HIGH"
        assert len(tc.sources) == 1
