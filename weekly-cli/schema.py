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
    # Case-insensitive exact match: models routinely emit "hypothesis" for
    # HYPOTHESIS, and rejecting that on capitalisation would throw away a
    # correct answer and substitute a wrong one.
    upper = v.upper()
    for valid in valid_values:
        if valid.upper() == upper:
            return valid
    # Substring match: if the valid value appears anywhere in the AI output
    for valid in sorted(valid_values, key=len, reverse=True):
        if valid.upper() in upper:
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

# "UNVERIFIED" is not an Admiralty grade.  It is the *absence* of one: a
# source we never obtained cannot be graded C3 (basic reliability, possibly
# true) because that reads as an assessment we never made.  Grade absence
# explicitly instead of defaulting to a plausible-looking middle grade.
UNVERIFIED_RELIABILITY = "UNVERIFIED"
UNVERIFIED_CREDIBILITY = 6  # Admiralty 6 == "cannot be corroborated"

_RELIABILITY_VALUES: frozenset[str] = frozenset(
    {"A", "B", "C", "D", "E", "F", UNVERIFIED_RELIABILITY}
)


class SourceGrade(BaseModel):
    """Source reliability and credibility assessment.

    reliability: A-F rating (analogous to intelligence source grading).
    credibility: 1-6 where 1=highest credibility, 6=unverifiable.
    rationale: Free-text explanation of the assessment.
    """

    reliability: str = Field(default=UNVERIFIED_RELIABILITY)
    credibility: int = Field(default=UNVERIFIED_CREDIBILITY, ge=1, le=6)
    rationale: str = ""

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Fuzzy-fix reliability enum.  Absent or unrecognised grades collapse
        # to UNVERIFIED rather than to a middle grade we never assessed.
        if "reliability" in data:
            data["reliability"] = _fuzzy_fix_enum(
                str(data.get("reliability", UNVERIFIED_RELIABILITY)),
                _RELIABILITY_VALUES,
                _RELIABILITY_FIXUPS,
                UNVERIFIED_RELIABILITY,
            )
        # Clamp and coerce credibility to int (LLM often returns floats)
        if "credibility" in data and isinstance(data["credibility"], (int, float)):
            val = int(data["credibility"])
            if val < 1:
                _logger.warning("  [sanitize] SourceGrade credibility=%s clamped to 1", val)
                data["credibility"] = 1
            elif val > 6:
                _logger.warning("  [sanitize] SourceGrade credibility=%s clamped to 6", val)
                data["credibility"] = 6
            else:
                data["credibility"] = val
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
    # ---- event identity (additive; absent on pre-v3 payloads) ----
    # A hot topic is a headline, an event is a thing that happened.  The same
    # event surfaces under different titles on different platforms, so it
    # carries a title-independent stable id plus its observation window.
    eventId: Optional[str] = None
    topicAliases: list[str] = Field(default_factory=list)
    sourcePlatform: Optional[str] = None
    firstSeenAt: Optional[str] = None
    lastSeenAt: Optional[str] = None
    eventStatus: Optional[str] = None


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
    # Structural interest is not the same as observed conduct.  A firm having
    # an incentive to cut costs does not establish that it did so here.
    relationshipType: str = "现实对抗"  # 现实对抗 | 潜在差异 | 共同利益
    evidenced: bool = False


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

# "证据不足" is a first-class answer, not a failure to answer.  Without it the
# schema forces a stage judgement on events whose material cannot support one.
INSUFFICIENT = "证据不足"

_CURRENT_PHASE_VALUES: frozenset[str] = frozenset(
    {"量变积累", "质的飞跃", "量变中的局部质变", INSUFFICIENT}
)


class UnityOfOpposites(BaseModel):
    """Unity of opposites analysis for a contradiction.

    `applicable=False` means this law does not usefully explain the event.
    A reliability-engineering failure is better served by engineering analysis
    than by a forced account of identity and struggle.
    """

    identity: str = ""
    struggle: str = ""
    particularity: str = ""
    universality: str = ""
    applicable: bool = True
    notApplicableReason: str = ""


class QuantityQuality(BaseModel):
    """Quantity-quality transformation analysis."""

    currentPhase: str = Field(default="量变积累")
    quantitativeDirection: str = ""
    measure: str = ""
    newQuality: Optional[str] = None
    oldQualityNegated: str = ""
    applicable: bool = True
    notApplicableReason: str = ""

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


_DIRECTION_VALUES: frozenset[str] = frozenset(
    {"螺旋上升", "暂时倒退", "停滞", INSUFFICIENT}
)


class NegationOfNegation(BaseModel):
    """Negation of negation analysis."""

    oldThing: str = ""
    firstNegation: str = ""
    internalNegation: str = ""
    direction: str = Field(default="螺旋上升")
    stageCharacteristics: str = ""
    applicable: bool = True
    notApplicableReason: str = ""

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
        # Coerce probability: LLM may return "55-80%" or "0.7" or other formats
        if "probability" in data:
            prob = data["probability"]
            if isinstance(prob, str):
                prob = prob.strip().rstrip("%")
                if "-" in prob:
                    # "55-80" → midpoint
                    parts = prob.split("-")
                    try:
                        lo, hi = float(parts[0]), float(parts[1])
                        prob = (lo + hi) / 200.0  # convert from percentage
                    except (ValueError, IndexError):
                        prob = 0.5
                else:
                    try:
                        prob = float(prob)
                        if prob > 1.0:
                            prob = prob / 100.0  # treat as percentage
                    except (ValueError, TypeError):
                        prob = 0.5
            elif isinstance(prob, (int, float)):
                if prob > 1.0:
                    prob = prob / 100.0
            else:
                prob = 0.5
            data["probability"] = max(0.0, min(1.0, float(prob)))
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

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Coerce float priority to int (LLM often returns 3.0 instead of 3)
        if "priority" in data and isinstance(data["priority"], float):
            data["priority"] = int(data["priority"])
        return data


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
    # A principal contradiction is a finding, not a required field.  When the
    # evidence does not identify one, saying so is the correct output.
    principalContradiction: str = ""
    principalContradictionUncertain: bool = False
    potentialContradictions: list[str] = Field(default_factory=list)
    commonInterests: list[str] = Field(default_factory=list)

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
# Evidence layer: claim typing, source records, dossiers
# =============================================================================
# The governing rule of this layer:
#
#   A source proves only the proposition it actually supports.
#
# A page being *related to* an event does not license every downstream
# inference drawn from that event.  So every key judgment carries an explicit
# type and an explicit verification status rather than silently inheriting the
# confidence of the material next to it.  In particular, an inference about
# someone's motive never inherits the confidence of the underlying fact that
# the incentive exists.

CLAIM_TYPES: frozenset[str] = frozenset(
    {
        "FACT",            # verifiable occurrence ("the company published X")
        "ATTRIBUTED",      # a statement with a named speaker ("the company says X")
        "INFERENCE",       # derived from facts, not itself reported
        "HYPOTHESIS",      # an explanation still awaiting test
        "VALUE_JUDGMENT",  # a normative position
        "UNKNOWN",         # currently undecidable
    }
)

VERIFICATION_STATUSES: frozenset[str] = frozenset(
    {"UNVERIFIED", "SINGLE_SOURCE", "CORROBORATED", "CONTRADICTED"}
)

PUBLICATION_DECISIONS: frozenset[str] = frozenset(
    {"KEEP", "QUALIFY", "REWRITE", "REMOVE", "RESEARCH", "UNREVIEWED"}
)

SOURCE_KINDS: frozenset[str] = frozenset(
    {
        "PRIMARY",      # the origin: announcement, filing, court doc, dataset
        "INDEPENDENT",  # original reporting by a party with no stake in the claim
        "REPUBLISHED",  # carrying someone else's report
        "UNKNOWN",
    }
)

EVENT_STATUSES: frozenset[str] = frozenset(
    {"新发生", "持续发展", "出现反转", "基本结束", "待观察"}
)

# Risk classes that demand a higher evidence bar before publication.  Claims
# in these classes are the ones that cause real harm when wrong: they assert
# what someone intended, what is illegal, or what caused what.
RISK_LEVELS: frozenset[str] = frozenset({"low", "medium", "high"})
HIGH_RISK_TYPES: frozenset[str] = frozenset({"HYPOTHESIS", "INFERENCE"})


class SourceRecord(BaseModel):
    """A captured source with provenance and a content fingerprint.

    `kind` records whether this is where the information originated or where
    it was merely repeated.  Five outlets carrying one announcement are five
    `REPUBLISHED` records, not five independent witnesses.
    """

    sourceId: str = ""
    url: str = ""
    title: str = ""
    publisher: str = ""
    publishedAt: Optional[str] = None
    retrievedAt: str = ""
    snippet: str = ""
    content: str = ""
    # Fingerprint of the retrieved body, so later runs can detect that a page
    # changed under us rather than silently re-reading it as the same source.
    contentFingerprint: str = ""
    kind: str = "UNKNOWN"
    reliability: str = UNVERIFIED_RELIABILITY
    credibility: int = UNVERIFIED_CREDIBILITY
    fetchStatus: str = "snippet-only"

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "kind" in data:
            data["kind"] = _fuzzy_fix_enum(
                str(data.get("kind", "UNKNOWN")), SOURCE_KINDS, {}, "UNKNOWN",
            )
        if "reliability" in data:
            data["reliability"] = _fuzzy_fix_enum(
                str(data.get("reliability", UNVERIFIED_RELIABILITY)),
                _RELIABILITY_VALUES,
                _RELIABILITY_FIXUPS,
                UNVERIFIED_RELIABILITY,
            )
        return data


class ClaimRecord(BaseModel):
    """A single assertion with its type, evidence, and publish decision.

    `path` locates the assertion inside the analysis tree (for example
    `events[0].materialContent`) so a revision directive can rewrite or
    delete exactly that sentence instead of vaguely criticising it.
    """

    claimId: str = ""
    eventId: str = ""
    statement: str = ""
    type: str = "UNKNOWN"
    path: str = ""
    evidenceIds: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    verificationStatus: str = "UNVERIFIED"
    publicationDecision: str = "UNREVIEWED"
    riskLevel: str = "low"
    reason: str = ""
    # Required for VALUE_JUDGMENT: the norm the judgment appeals to, so it is
    # not smuggled in as though it were a plain factual observation.
    valuePrinciple: str = ""
    revisedStatement: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "type" in data:
            data["type"] = _fuzzy_fix_enum(
                str(data.get("type", "UNKNOWN")), CLAIM_TYPES, {}, "UNKNOWN",
            )
        if "verificationStatus" in data:
            data["verificationStatus"] = _fuzzy_fix_enum(
                str(data.get("verificationStatus", "UNVERIFIED")),
                VERIFICATION_STATUSES, {}, "UNVERIFIED",
            )
        if "publicationDecision" in data:
            data["publicationDecision"] = _fuzzy_fix_enum(
                str(data.get("publicationDecision", "UNREVIEWED")),
                PUBLICATION_DECISIONS, {}, "UNREVIEWED",
            )
        if "riskLevel" in data:
            data["riskLevel"] = _fuzzy_fix_enum(
                str(data.get("riskLevel", "low")), RISK_LEVELS, {}, "low",
            )
        return data

    @property
    def publishable(self) -> bool:
        """True when this claim may appear in the published article as-is."""
        return self.publicationDecision in ("KEEP",)


class TimelineEntry(BaseModel):
    """One dated step in an event's development."""

    occurredAt: str = ""
    description: str = ""
    sourceIds: list[str] = Field(default_factory=list)


class EvidenceDossier(BaseModel):
    """The fact file for one event, assembled *before* deep analysis.

    This is the object the dialectical phases read from.  It exists so the
    analysis starts from retrieved material rather than from a headline and a
    heat ranking.
    """

    eventId: str = ""
    title: str = ""
    queries: list[str] = Field(default_factory=list)
    sources: list[SourceRecord] = Field(default_factory=list)
    claims: list[ClaimRecord] = Field(default_factory=list)
    # Facts on which sources actively disagree.
    conflicts: list[str] = Field(default_factory=list)
    # Key questions the retrieved material does not answer.
    unknowns: list[str] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    retrievedAt: str = ""
    searchFailed: bool = False

    def source_by_id(self, source_id: str) -> Optional[SourceRecord]:
        for s in self.sources:
            if s.sourceId == source_id:
                return s
        return None

    @property
    def independent_count(self) -> int:
        """Number of distinct-origin sources (republications excluded)."""
        return sum(1 for s in self.sources if s.kind in ("PRIMARY", "INDEPENDENT"))

    @property
    def has_primary(self) -> bool:
        return any(s.kind == "PRIMARY" for s in self.sources)


class RevisionRecord(BaseModel):
    """One applied revision, kept so a judgment change is auditable."""

    claimId: str = ""
    eventId: str = ""
    path: str = ""
    action: str = "UNREVIEWED"
    before: str = ""
    after: str = ""
    reason: str = ""
    round: int = 1


class PublicationGate(BaseModel):
    """Deterministic publish/no-publish decision with its reasons."""

    decision: str = "ALLOW"  # ALLOW | DEGRADE | BLOCK
    reasons: list[str] = Field(default_factory=list)
    blockingClaims: list[str] = Field(default_factory=list)
    degradedClaims: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "decision" in data:
            data["decision"] = _fuzzy_fix_enum(
                str(data.get("decision", "ALLOW")),
                frozenset({"ALLOW", "DEGRADE", "BLOCK"}),
                {},
                "ALLOW",
            )
        return data


# =============================================================================
# Evidence trace and metadata models
# =============================================================================


class TracedSource(BaseModel):
    """A single source reference with reliability metadata."""

    sourceName: str = ""
    sourceUrl: str = ""
    reliability: str = Field(default=UNVERIFIED_RELIABILITY)
    credibility: int = Field(default=UNVERIFIED_CREDIBILITY, ge=1, le=6)

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "reliability" in data:
            data["reliability"] = _fuzzy_fix_enum(
                str(data.get("reliability", UNVERIFIED_RELIABILITY)),
                _RELIABILITY_VALUES,
                _RELIABILITY_FIXUPS,
                UNVERIFIED_RELIABILITY,
            )
        if "credibility" in data and isinstance(data["credibility"], (int, float)):
            val = int(data["credibility"])
            if val < 1:
                data["credibility"] = 1
            elif val > 6:
                data["credibility"] = 6
            else:
                data["credibility"] = val
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
    # ---- reproducibility trail (additive) ----
    analysisDate: str = ""       # when this run executed
    evidenceCutoff: str = ""     # latest retrieval timestamp feeding the analysis
    promptVersion: str = ""      # hash of the prompt set used
    pipelineVersion: str = "v3"


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
    # ---- v3 evidence layer (additive; empty on pre-v3 payloads) ----
    evidence: list[EvidenceDossier] = Field(default_factory=list)
    revisionLog: list[RevisionRecord] = Field(default_factory=list)
    publicationGate: Optional[PublicationGate] = None

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
SourceRecord.model_rebuild()
ClaimRecord.model_rebuild()
TimelineEntry.model_rebuild()
EvidenceDossier.model_rebuild()
RevisionRecord.model_rebuild()
PublicationGate.model_rebuild()
WeeklyIssue.model_rebuild()
