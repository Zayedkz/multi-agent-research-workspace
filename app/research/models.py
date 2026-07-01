from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class SourceType(StrEnum):
    academic = "academic"
    government = "government"
    news = "news"
    company = "company"
    blog = "blog"
    social = "social"
    unknown = "unknown"


class ResearchProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    question: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sources: list["ResearchSource"] = Field(default_factory=list)


class ResearchSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    title: str = Field(min_length=1)
    url: HttpUrl
    source_type: SourceType = SourceType.unknown
    author: str | None = None
    published_at: datetime | None = None
    summary: str = Field(min_length=1)
    key_claims: list[str] = Field(default_factory=list)
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CredibilityAssessment(BaseModel):
    source_id: str
    score: float = Field(ge=0, le=1)
    label: str
    reasons: list[str]


class EvidenceCard(BaseModel):
    source_id: str
    title: str
    url: HttpUrl
    claim: str
    credibility_score: float


class ResearchBrief(BaseModel):
    project_id: str
    question: str
    source_count: int
    average_credibility: float
    answer: str
    evidence: list[EvidenceCard]
    gaps: list[str]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
