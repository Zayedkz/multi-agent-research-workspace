from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from app.research.brief import DeterministicBriefGenerator
from app.research.credibility import DeterministicCredibilityScorer
from app.research.models import CredibilityAssessment, ResearchBrief, ResearchSource, SourceType
from app.research.store import research_store

router = APIRouter(prefix="/research", tags=["research"])


class CreateProjectRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class CreateProjectResponse(BaseModel):
    project_id: str
    question: str


class AddSourceRequest(BaseModel):
    title: str = Field(min_length=1)
    url: HttpUrl
    source_type: SourceType = SourceType.unknown
    author: str | None = None
    published_at: datetime | None = None
    summary: str = Field(min_length=1)
    key_claims: list[str] = Field(default_factory=list)


class AddSourceResponse(BaseModel):
    project_id: str
    source_id: str
    source_count: int
    credibility: CredibilityAssessment


@router.post("/projects", response_model=CreateProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(request: CreateProjectRequest) -> CreateProjectResponse:
    project = research_store.create_project(request.question)
    return CreateProjectResponse(project_id=project.id, question=project.question)


@router.post(
    "/projects/{project_id}/sources",
    response_model=AddSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_source(project_id: str, request: AddSourceRequest) -> AddSourceResponse:
    source = ResearchSource(
        project_id=project_id,
        title=request.title,
        url=request.url,
        source_type=request.source_type,
        author=request.author,
        published_at=request.published_at,
        summary=request.summary,
        key_claims=request.key_claims,
    )
    project = research_store.add_source(source)
    credibility = DeterministicCredibilityScorer().assess(source)
    return AddSourceResponse(
        project_id=project.id,
        source_id=source.id,
        source_count=len(project.sources),
        credibility=credibility,
    )


@router.get("/projects/{project_id}/brief", response_model=ResearchBrief)
def get_brief(project_id: str) -> ResearchBrief:
    project = research_store.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="research project not found",
        )

    return DeterministicBriefGenerator().generate(project)
