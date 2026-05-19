from typing import Literal, Optional
from pydantic import BaseModel, Field


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


class Event(BaseModel):
    id: str
    title: str
    impactScore: int = Field(ge=1, le=5)
    infoGainScore: int = Field(ge=1, le=5)
    summary: str
    classAnalysis: ClassAnalysis = Field(default_factory=ClassAnalysis)
    dialecticalSummary: str = ""
    timeline: list[TimelineNode] = Field(default_factory=list)
    evidence: list[EvidenceNode] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)


class WeeklyIssue(BaseModel):
    id: str
    weekStart: str
    weekEnd: str
    events: list[Event] = Field(default_factory=list)
