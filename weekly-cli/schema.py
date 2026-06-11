from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---- Pipeline intermediate models ----

class RawEvent(BaseModel):
    """Phase 0 输出：原始抓取事件"""
    title: str
    summary: str


class CensoredEvent(BaseModel):
    """Phase 1 输出：通过政审的事件"""
    title: str
    summary: str


class ScoredEvent(BaseModel):
    """Phase 2 输出：评分后入选的事件"""
    title: str
    summary: str
    impactScore: int = Field(ge=1, le=5)
    infoGainScore: int = Field(ge=1, le=5)


# ---- Output models ----


class ClassAnalysis(BaseModel):
    classNature: str = ""
    contradiction: str = ""
    historicalContext: str = ""


class TimelineNode(BaseModel):
    id: str
    time: str
    title: str
    description: str
    evidenceRefs: list[str] = Field(default_factory=list)


class EvidenceNode(BaseModel):
    id: str
    sourceType: Literal["官媒", "社交平台", "一手材料", "其他"]
    sourceName: str
    sourceUrl: Optional[str] = None
    content: str
    authenticity: Literal["真实", "存疑", "不实", "待验证"]
    aiReason: str
    classBias: Literal["无产阶级立场", "资产阶级立场", "小资产阶级立场", "帝国主义话语", "待判断"] = "待判断"


class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: Literal["因果", "关联", "矛盾"]
    description: str

    model_config = {"populate_by_name": True}


# ---- Phase 4: Synthesis models ----


class CrossCuttingTheme(BaseModel):
    name: str = Field(max_length=80)
    description: str = Field(max_length=500)
    relatedEventIds: list[str] = Field(default_factory=list)
    significance: str = Field(max_length=500)


class IdentifiedTrend(BaseModel):
    name: str = Field(max_length=80)
    description: str = Field(max_length=500)
    direction: Literal["上升", "下降", "转型", "激化", "缓和"]
    evidenceEventIds: list[str] = Field(default_factory=list)


class ContradictionInMotion(BaseModel):
    contradiction: str = Field(max_length=300)
    opposingForces: str = Field(max_length=500)
    eventsInvolved: list[str] = Field(default_factory=list)
    currentState: Literal["对抗激化", "暂时缓和", "向新形态转化", "隐性积累"]
    outlook: str = Field(max_length=500)


class WeeklySynthesis(BaseModel):
    weeklyNarrative: str = Field(max_length=2000)
    crossCuttingThemes: list[CrossCuttingTheme] = Field(default_factory=list, max_length=5)
    trends: list[IdentifiedTrend] = Field(default_factory=list, max_length=5)
    contradictionsInMotion: list[ContradictionInMotion] = Field(default_factory=list, max_length=5)
    globalAssessment: str = Field(default="", max_length=1000)
    dataGaps: list[str] = Field(default_factory=list, max_length=5)


class Event(BaseModel):
    id: str = Field(max_length=100)
    title: str = Field(max_length=500)
    impactScore: int = Field(ge=1, le=5)
    infoGainScore: int = Field(ge=1, le=5)
    summary: str = Field(max_length=5000)
    classAnalysis: ClassAnalysis = Field(default_factory=ClassAnalysis)
    dialecticalSummary: str = Field(default="", max_length=200)
    timeline: list[TimelineNode] = Field(default_factory=list, max_length=50)
    evidence: list[EvidenceNode] = Field(default_factory=list, max_length=100)
    edges: list[Edge] = Field(default_factory=list, max_length=200)


class WeeklyIssue(BaseModel):
    id: str
    weekStart: str
    weekEnd: str
    events: list[Event] = Field(default_factory=list)
    synthesis: WeeklySynthesis | None = Field(default=None)
