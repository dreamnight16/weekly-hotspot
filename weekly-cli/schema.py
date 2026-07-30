"""Pydantic v2 data models for 格物 (Dianalyze) v2 dialectical analysis system.

Five-phase dialectical materialism analysis pipeline:
  Phase 1 - Phenomenon Grasping (现象把握): empirical event collection
  Phase 2 - Contradiction Identification (矛盾识别): interest + class analysis
  Phase 3 - Dialectical Unfolding (辩证展开): unity of opposites, quantity-quality,
             negation of negation
  Phase 4 - Historical Positioning (历史定位): epoch themes, archetypes, analogies
  Phase 5 - Practice Orientation (实践导向): scenarios, signals, calibration

All models use Pydantic v2 with:
  - model_validator(mode="before") for enum sanitization + score clamping
  - model_validator(mode="after") for cross-reference validation
  - _fuzzy_fix_enum() helper for AI output sanitization
"""

from __future__ import annotations

import logging
from typing import Any, Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator

try:
    from config import get_logger

    _logger = get_logger("schema")
except ImportError:
    _logger = logging.getLogger("schema")


# =============================================================================
# Enum value fixup maps
# =============================================================================
# These maps correct known AI mistakes in enum outputs.  Extend them as new
# patterns are discovered in production logs.

_RELIABILITY_FIXUPS: dict[str, str] = {}
_CREDIBILITY_FIXUPS: dict[str, str] = {}
_CURRENT_PHASE_FIXUPS: dict[str, str] = {}
_DIRECTION_FIXUPS: dict[str, str] = {}
_CONFIDENCE_FIXUPS: dict[str, str] = {}
_ARCHETYPE_FIXUPS: dict[str, str] = {}
_SCENARIO_TYPE_FIXUPS: dict[str, str] = {}


def _fuzzy_fix_enum(
    value: str,
    valid_values: frozenset[str],
    fixups: dict[str, str],
    default: str,
) -> str:
    """Try to map a non-enum value to a valid one.  Strips whitespace first.

    Strategy (in order):
      1. Exact match after stripping
      2. Exact match in fixup map
      3. Substring: valid value appears anywhere in the AI output
      4. Fall back to default

    Args:
        value: The raw AI-generated value.
        valid_values: The set of acceptable enum values.
        fixups: Known-error -> correct-value mapping.
        default: Value to return when no match is found.

    Returns:
        A value guaranteed to be in valid_values or equal to default.
    """
    if not isinstance(value, str):
        return default
    v = value.strip()
    if v in valid_values:
        return v
    if v in fixups:
        return fixups[v]
    # Substring match: if the valid value appears anywhere in the AI output
    for valid in sorted(valid_values, key=len, reverse=True):
        if valid in v:
            _logger.warning(
                "  [sanitize] enum fixup: %r -> %r (substring match)", v, valid
            )
            return valid
    _logger.warning(
        "  [sanitize] enum default: %r -> %r (no match in %s)",
        v,
        default,
        sorted(valid_values),
    )
    return default


# =============================================================================
# Phase 0-1: Pipeline intermediate models
# =============================================================================


class RawEvent(BaseModel):
    """Phase 0 output: raw scraped event."""

    title: str
    summary: str


class CensoredEvent(BaseModel):
    """Phase 1 intermediate: censorship-passed event."""

    title: str
    summary: str


# =============================================================================
# Phase 1: Phenomenon Grasping (现象把握) - Empirical models
# =============================================================================

_RELIABILITY_VALUES: frozenset[str] = frozenset({"A", "B", "C", "D", "E", "F"})


class SourceGrade(BaseModel):
    """Source reliability and credibility assessment.

    reliability: A-F rating (analogous to intelligence source grading).
    credibility: 1-6 where 1=highest credibility, 6=unverifiable.
    rationale: Free-text explanation of the assessment.
    """

    reliability: str = Field(default="C")
    credibility: int = Field(default=3, ge=1, le=6)
    rationale: str = ""

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Fuzzy-fix reliability enum
        if "reliability" in data:
            data["reliability"] = _fuzzy_fix_enum(
                str(data.get("reliability", "C")),
                _RELIABILITY_VALUES,
                _RELIABILITY_FIXUPS,
                "C",
            )
        # Clamp credibility
        if "credibility" in data and isinstance(data["credibility"], (int, float)):
            val = data["credibility"]
            if val < 1:
                _logger.warning("  [sanitize] SourceGrade credibility=%s clamped to 1", val)
                data["credibility"] = 1
            elif val > 6:
                _logger.warning("  [sanitize] SourceGrade credibility=%s clamped to 6", val)
                data["credibility"] = 6
        return data


class GDELTBaseline(BaseModel):
    """GDELT baseline metrics for the week."""

    totalArticles: int = 0
    avgTone: float = 0.0
    numEvents: int = 0
    period: str = ""


class SelectedEvent(BaseModel):
    """Phase 1 output: event selected for dialectical analysis.

    An event passes through empirical filtering and is found to have material
    interest content worth analyzing.
    """

    id: str
    title: str
    summary: str
    sourceUrl: Optional[str] = None
    materialContent: str = ""
    isDirectExpression: bool = False
    sourceGrade: Optional[SourceGrade] = None


class ExcludedEvent(BaseModel):
    """Phase 1 output: event excluded from further analysis."""

    id: str
    title: str
    summary: str
    exclusionReason: str = ""


# =============================================================================
# Phase 2: Contradiction Identification (矛盾识别) - Analysis models
# =============================================================================


class InterestStructure(BaseModel):
    """Material interest structure analysis for a stakeholder group."""

    interestGroup: str = ""
    materialInterest: str = ""
    expressionForm: str = ""
    intensity: int = Field(default=3, ge=1, le=5)
    relatedEventIds: list[str] = Field(default_factory=list)


class ClassPosition(BaseModel):
    """Class position analysis in production relations."""

    className: str = ""
    position: str = ""
    coreInterest: str = ""
    contradictions: list[str] = Field(default_factory=list)
    relatedEventIds: list[str] = Field(default_factory=list)


class NineDimScores(BaseModel):
    """Nine-dimensional dialectical score assessment.

    Each dimension is a (score, confidence) tuple where:
      - score: 1-10 integer
      - confidence: 0.0-1.0 float
    """

    magnitude: tuple[int, float] = (5, 0.5)
    scope: tuple[int, float] = (5, 0.5)
    velocity: tuple[int, float] = (5, 0.5)
    novelty: tuple[int, float] = (5, 0.5)
    cascadePotential: tuple[int, float] = (5, 0.5)
    actorProminence: tuple[int, float] = (5, 0.5)
    uncertainty: tuple[int, float] = (5, 0.5)
    polarity: tuple[int, float] = (5, 0.5)
    durability: tuple[int, float] = (5, 0.5)

    @model_validator(mode="before")
    @classmethod
    def _clamp_scores(cls, data: Any) -> Any:
        """Clamp each dimension's score to [1,10] and confidence to [0.0,1.0]."""
        if not isinstance(data, dict):
            return data
        for field_name in (
            "magnitude", "scope", "velocity", "novelty",
            "cascadePotential", "actorProminence", "uncertainty",
            "polarity", "durability",
        ):
            if field_name in data:
                val = data[field_name]
                if isinstance(val, (list, tuple)) and len(val) >= 2:
                    score, conf = val[0], val[1]
                    score = max(1, min(10, int(score)))
                    conf = max(0.0, min(1.0, float(conf)))
                    data[field_name] = (score, conf)
        return data


class CompetingHypothesis(BaseModel):
    """Competing explanatory hypothesis with evidence assessment."""

    hypothesisId: str = ""
    description: str = ""
    supportingEvidence: str = ""
    contradictingEvidence: str = ""
    assessedProbability: float = Field(default=0.5, ge=0.0, le=1.0)
    relatedEventIds: list[str] = Field(default_factory=list)


# =============================================================================
# Phase 3: Dialectical Unfolding (辩证展开) - Dialectical models
# =============================================================================

_CURRENT_PHASE_VALUES: frozenset[str] = frozenset(
    {"量变积累", "质的飞跃", "量变中的局部质变"}
)


class UnityOfOpposites(BaseModel):
    """Unity of opposites analysis for a contradiction."""

    identity: str = ""
    struggle: str = ""
    particularity: str = ""
    universality: str = ""


class QuantityQuality(BaseModel):
    """Quantity-quality transformation analysis."""

    currentPhase: str = Field(default="量变积累")
    quantitativeDirection: str = ""
    measure: str = ""
    newQuality: Optional[str] = None
    oldQualityNegated: str = ""

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "currentPhase" in data:
            data["currentPhase"] = _fuzzy_fix_enum(
                str(data.get("currentPhase", "量变积累")),
                _CURRENT_PHASE_VALUES,
                _CURRENT_PHASE_FIXUPS,
                "量变积累",
            )
        return data


_DIRECTION_VALUES: frozenset[str] = frozenset({"螺旋上升", "暂时倒退", "停滞"})


class NegationOfNegation(BaseModel):
    """Negation of negation analysis."""

    oldThing: str = ""
    firstNegation: str = ""
    internalNegation: str = ""
    direction: str = Field(default="螺旋上升")
    stageCharacteristics: str = ""

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "direction" in data:
            data["direction"] = _fuzzy_fix_enum(
                str(data.get("direction", "螺旋上升")),
                _DIRECTION_VALUES,
                _DIRECTION_FIXUPS,
                "螺旋上升",
            )
        return data


_CONFIDENCE_VALUES: frozenset[str] = frozenset({"HIGH", "MEDIUM", "LOW"})


class AdversarialReview(BaseModel):
    """Adversarial review of a dialectical claim."""

    reviewAspect: str = ""
    originalClaim: str = ""
    critique: str = ""
    revisedClaim: Optional[str] = None
    confidence: str = Field(default="MEDIUM")

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "confidence" in data:
            data["confidence"] = _fuzzy_fix_enum(
                str(data.get("confidence", "MEDIUM")),
                _CONFIDENCE_VALUES,
                _CONFIDENCE_FIXUPS,
                "MEDIUM",
            )
        return data


class CausalLoopDiagram(BaseModel):
    """Causal loop diagram representing feedback structures."""

    diagramId: str = ""
    description: str = ""
    nodes: list[str] = Field(default_factory=list)
    positiveFeedbackLoops: list[str] = Field(default_factory=list)
    negativeFeedbackLoops: list[str] = Field(default_factory=list)
    keyLeveragePoints: list[str] = Field(default_factory=list)


class DataValidation(BaseModel):
    """Data validation check result."""

    validationCheck: str = ""
    dataSource: str = ""
    result: str = ""
    issues: list[str] = Field(default_factory=list)
    confidence: str = Field(default="HIGH")

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "confidence" in data:
            data["confidence"] = _fuzzy_fix_enum(
                str(data.get("confidence", "HIGH")),
                _CONFIDENCE_VALUES,
                _CONFIDENCE_FIXUPS,
                "HIGH",
            )
        return data


# =============================================================================
# Phase 4: Historical Positioning (历史定位) - Historical models
# =============================================================================


class EpochTheme(BaseModel):
    """A theme characteristic of the current historical epoch."""

    themeName: str = ""
    description: str = ""
    relevanceToCurrentEvents: str = ""
    relatedEventIds: list[str] = Field(default_factory=list)


_ARCHETYPE_VALUES: frozenset[str] = frozenset(
    {"FixesThatFail", "LimitsToGrowth", "ShiftingTheBurden", "TragedyOfCommons"}
)


class SystemArchetype(BaseModel):
    """Systems thinking archetype identified in the current situation."""

    archetypeType: str = Field(default="LimitsToGrowth")
    patternName: str = ""
    description: str = ""
    structuralFeatures: str = ""
    relatedEventIds: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "archetypeType" in data:
            data["archetypeType"] = _fuzzy_fix_enum(
                str(data.get("archetypeType", "LimitsToGrowth")),
                _ARCHETYPE_VALUES,
                _ARCHETYPE_FIXUPS,
                "LimitsToGrowth",
            )
        return data


class HiddenConnection(BaseModel):
    """A non-obvious connection between seemingly unrelated phenomena."""

    connectionName: str = ""
    entityA: str = ""
    entityB: str = ""
    connectionMechanism: str = ""
    significance: str = ""
    relatedEventIds: list[str] = Field(default_factory=list)


class HistoricalAnalogy(BaseModel):
    """Historical analogy for understanding the current situation."""

    analogyName: str = ""
    historicalPeriod: str = ""
    historicalEvent: str = ""
    similarity: str = ""
    difference: str = ""
    lessonForToday: str = ""
    relatedEventIds: list[str] = Field(default_factory=list)


# =============================================================================
# Phase 5: Practice Orientation (实践导向) - Forward-looking models
# =============================================================================

_SCENARIO_TYPE_VALUES: frozenset[str] = frozenset(
    {"baseline", "alternative", "wildcard"}
)


class Scenario(BaseModel):
    """Forward-looking scenario for practice guidance."""

    scenarioId: str = ""
    title: str = ""
    description: str = ""
    scenarioType: str = Field(default="baseline")
    probability: float = Field(default=0.5, ge=0.0, le=1.0)
    keyAssumptions: list[str] = Field(default_factory=list)
    earlySignals: list[str] = Field(default_factory=list)
    relatedEventIds: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "scenarioType" in data:
            data["scenarioType"] = _fuzzy_fix_enum(
                str(data.get("scenarioType", "baseline")),
                _SCENARIO_TYPE_VALUES,
                _SCENARIO_TYPE_FIXUPS,
                "baseline",
            )
        return data


class WatchSignal(BaseModel):
    """A signal to watch for scenario validation in coming weeks."""

    signalName: str = ""
    description: str = ""
    indicator: str = ""
    currentValue: str = ""
    threshold: str = ""
    trend: str = ""
    priority: int = Field(default=3, ge=1, le=5)


class LastWeekCalibration(BaseModel):
    """Calibration against last week's predictions."""

    predictionSummary: str = ""
    actualOutcome: str = ""
    calibrationNote: str = ""
    accuracyScore: Optional[float] = None


# =============================================================================
# Phase aggregate models (one per pipeline phase)
# =============================================================================


class PhenomenonGrasping(BaseModel):
    """Phase 1 aggregate: empirical phenomenon grasping output."""

    phaseSummary: str = ""
    selectedEvents: list[SelectedEvent] = Field(default_factory=list)
    excludedEvents: list[ExcludedEvent] = Field(default_factory=list)
    gdeltBaseline: Optional[GDELTBaseline] = None
    sourceQualityReport: str = ""

    @model_validator(mode="after")
    def _filter_empty(self) -> Self:
        # Phase 1 has no empty-ref filtering needed for events
        return self


class ContradictionIdentification(BaseModel):
    """Phase 2 aggregate: contradiction identification output."""

    phaseSummary: str = ""
    events: list[SelectedEvent] = Field(default_factory=list)
    overallContradictionLandscape: str = ""
    interestStructures: list[InterestStructure] = Field(default_factory=list)
    classPositions: list[ClassPosition] = Field(default_factory=list)
    nineDimScores: Optional[NineDimScores] = None
    competingHypotheses: list[CompetingHypothesis] = Field(default_factory=list)

    @model_validator(mode="after")
    def _filter_empty_refs(self) -> Self:
        self.interestStructures = [
            i for i in self.interestStructures if i.relatedEventIds
        ]
        self.classPositions = [
            c for c in self.classPositions if c.relatedEventIds
        ]
        self.competingHypotheses = [
            h for h in self.competingHypotheses if h.relatedEventIds
        ]
        return self


class DialecticalUnfolding(BaseModel):
    """Phase 3 aggregate: dialectical unfolding output."""

    phaseSummary: str = ""
    events: list[SelectedEvent] = Field(default_factory=list)
    dialecticalConfidence: str = Field(default="MEDIUM")
    unityOfOpposites: Optional[UnityOfOpposites] = None
    quantityQuality: Optional[QuantityQuality] = None
    negationOfNegation: Optional[NegationOfNegation] = None
    adversarialReview: Optional[AdversarialReview] = None
    causalLoopDiagram: Optional[CausalLoopDiagram] = None
    dataValidation: Optional[DataValidation] = None

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "dialecticalConfidence" in data:
            data["dialecticalConfidence"] = _fuzzy_fix_enum(
                str(data.get("dialecticalConfidence", "MEDIUM")),
                _CONFIDENCE_VALUES,
                _CONFIDENCE_FIXUPS,
                "MEDIUM",
            )
        return data

    @model_validator(mode="after")
    def _filter_empty(self) -> Self:
        return self


class HistoricalPositioning(BaseModel):
    """Phase 4 aggregate: historical positioning output."""

    phaseSummary: str = ""
    events: list[SelectedEvent] = Field(default_factory=list)
    crossCuttingSynthesis: Optional[str] = None
    epochThemes: list[EpochTheme] = Field(default_factory=list)
    systemArchetypes: list[SystemArchetype] = Field(default_factory=list)
    hiddenConnections: list[HiddenConnection] = Field(default_factory=list)
    historicalAnalogies: list[HistoricalAnalogy] = Field(default_factory=list)

    @model_validator(mode="after")
    def _filter_empty_refs(self) -> Self:
        self.epochThemes = [t for t in self.epochThemes if t.relatedEventIds]
        self.systemArchetypes = [
            a for a in self.systemArchetypes if a.relatedEventIds
        ]
        self.hiddenConnections = [
            c for c in self.hiddenConnections if c.relatedEventIds
        ]
        self.historicalAnalogies = [
            a for a in self.historicalAnalogies if a.relatedEventIds
        ]
        return self


class PracticeOrientation(BaseModel):
    """Phase 5 aggregate: practice orientation output."""

    overallJudgment: str = ""
    scenarios: list[Scenario] = Field(default_factory=list)
    practiceSignificance: str = ""
    signalsToWatch: list[WatchSignal] = Field(default_factory=list)
    lastWeekCalibration: Optional[LastWeekCalibration] = None

    @model_validator(mode="after")
    def _filter_empty_refs(self) -> Self:
        self.scenarios = [s for s in self.scenarios if s.relatedEventIds]
        return self


# =============================================================================
# Evidence trace and metadata models
# =============================================================================


class TracedSource(BaseModel):
    """A single source reference with reliability metadata."""

    sourceName: str = ""
    sourceUrl: str = ""
    reliability: str = Field(default="C")
    credibility: int = Field(default=3, ge=1, le=6)

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "reliability" in data:
            data["reliability"] = _fuzzy_fix_enum(
                str(data.get("reliability", "C")),
                _RELIABILITY_VALUES,
                _RELIABILITY_FIXUPS,
                "C",
            )
        if "credibility" in data and isinstance(data["credibility"], (int, float)):
            val = data["credibility"]
            if val < 1:
                data["credibility"] = 1
            elif val > 6:
                data["credibility"] = 6
        return data


class TracedClaim(BaseModel):
    """A verifiable claim with source tracing."""

    claimId: str = ""
    claim: str = ""
    phase: str = ""
    confidence: str = Field(default="MEDIUM")
    sources: list[TracedSource] = Field(default_factory=list)
    independentCorroborations: int = 0
    verificationMethod: str = ""

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "confidence" in data:
            data["confidence"] = _fuzzy_fix_enum(
                str(data.get("confidence", "MEDIUM")),
                _CONFIDENCE_VALUES,
                _CONFIDENCE_FIXUPS,
                "MEDIUM",
            )
        return data


class EvidenceTrace(BaseModel):
    """Complete evidence trace for an analysis issue."""

    claims: list[TracedClaim] = Field(default_factory=list)
    totalVerifiedClaims: int = 0


class IssueMetadata(BaseModel):
    """Run-level metadata for an analysis issue."""

    modelVersions: dict[str, str] = Field(default_factory=dict)
    verificationPasses: int = 0
    empiricalDegradations: list[str] = Field(default_factory=list)
    totalApiCost: float = 0.0
    runDuration: float = 0.0
    runId: str = ""


# =============================================================================
# Top-level WeeklyIssue model
# =============================================================================


class WeeklyIssue(BaseModel):
    """Top-level weekly dialectical analysis output.

    Contains all five phases of analysis plus evidence tracing and metadata.
    Phases 2-5 may be None if the pipeline did not execute them (e.g. if
    no events survived Phase 1 filtering).
    """

    id: str
    weekStart: str
    weekEnd: str
    events: list[SelectedEvent] = Field(default_factory=list)
    phase1: PhenomenonGrasping
    phase2: Optional[ContradictionIdentification] = None
    phase3: Optional[DialecticalUnfolding] = None
    phase4: Optional[HistoricalPositioning] = None
    phase5: Optional[PracticeOrientation] = None
    evidenceTrace: EvidenceTrace = Field(default_factory=EvidenceTrace)
    metadata: IssueMetadata = Field(default_factory=IssueMetadata)

    @model_validator(mode="after")
    def _validate_cross_phase_refs(self) -> Self:
        """Validate cross-phase event id references.

        Events referenced in later phases should exist in the events list.
        Missing references are logged but not removed (they may refer to
        events that were excluded after filtering).
        """
        event_ids = {e.id for e in self.events}
        all_events: set[str] = set()
        # Collect ids from phase 1
        all_events.update(e.id for e in self.phase1.selectedEvents)

        # Check phase 2 event refs
        if self.phase2 is not None:
            for e in self.phase2.events:
                if e.id and e.id not in all_events:
                    all_events.add(e.id)

        # Check phase 3 event refs
        if self.phase3 is not None:
            for e in self.phase3.events:
                if e.id and e.id not in all_events:
                    all_events.add(e.id)

        # Check phase 4 event refs
        if self.phase4 is not None:
            for e in self.phase4.events:
                if e.id and e.id not in all_events:
                    all_events.add(e.id)

        return self


# =============================================================================
# Rebuild forward references (needed for Pydantic v2 in some configurations)
# =============================================================================

RawEvent.model_rebuild()
CensoredEvent.model_rebuild()
SourceGrade.model_rebuild()
GDELTBaseline.model_rebuild()
SelectedEvent.model_rebuild()
ExcludedEvent.model_rebuild()
InterestStructure.model_rebuild()
ClassPosition.model_rebuild()
NineDimScores.model_rebuild()
CompetingHypothesis.model_rebuild()
UnityOfOpposites.model_rebuild()
QuantityQuality.model_rebuild()
NegationOfNegation.model_rebuild()
AdversarialReview.model_rebuild()
CausalLoopDiagram.model_rebuild()
DataValidation.model_rebuild()
EpochTheme.model_rebuild()
SystemArchetype.model_rebuild()
HiddenConnection.model_rebuild()
HistoricalAnalogy.model_rebuild()
Scenario.model_rebuild()
WatchSignal.model_rebuild()
LastWeekCalibration.model_rebuild()
PhenomenonGrasping.model_rebuild()
ContradictionIdentification.model_rebuild()
DialecticalUnfolding.model_rebuild()
HistoricalPositioning.model_rebuild()
PracticeOrientation.model_rebuild()
TracedSource.model_rebuild()
TracedClaim.model_rebuild()
EvidenceTrace.model_rebuild()
IssueMetadata.model_rebuild()
WeeklyIssue.model_rebuild()
