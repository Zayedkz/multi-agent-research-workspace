from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.research.brief import DeterministicBriefGenerator
from app.research.credibility import DeterministicCredibilityScorer
from app.research.models import (
    CredibilityAssessment,
    ResearchBrief,
    ResearchSource,
    SourceStatus,
    SourceType,
)
from app.research.store import sqlalchemy_research_store

router = APIRouter(prefix="/research", tags=["research"])
DbSession = Depends(get_db_session)


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
    created: bool
    source_count: int
    status: SourceStatus
    credibility: CredibilityAssessment


class ReviewSourceRequest(BaseModel):
    status: SourceStatus
    review_note: str | None = Field(default=None, max_length=1000)


class ReviewSourceResponse(BaseModel):
    project_id: str
    source_id: str
    status: SourceStatus
    review_note: str | None


@router.post("/projects", response_model=CreateProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest,
    session: Session = DbSession,
) -> CreateProjectResponse:
    project = sqlalchemy_research_store.create_project(session, request.question)
    return CreateProjectResponse(project_id=project.id, question=project.question)


@router.post(
    "/projects/{project_id}/sources",
    response_model=AddSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_source(
    project_id: str,
    request: AddSourceRequest,
    session: Session = DbSession,
) -> AddSourceResponse:
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
    result = sqlalchemy_research_store.add_source(session, source)
    credibility = DeterministicCredibilityScorer().assess(result.source)
    return AddSourceResponse(
        project_id=result.project.id,
        source_id=result.source.id,
        created=result.created,
        source_count=len(result.project.sources),
        status=result.source.status,
        credibility=credibility,
    )


@router.patch(
    "/projects/{project_id}/sources/{source_id}/review",
    response_model=ReviewSourceResponse,
)
def review_source(
    project_id: str,
    source_id: str,
    request: ReviewSourceRequest,
    session: Session = DbSession,
) -> ReviewSourceResponse:
    source = sqlalchemy_research_store.update_source_status(
        session,
        project_id,
        source_id,
        request.status,
        request.review_note,
    )
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="research source not found",
        )

    return ReviewSourceResponse(
        project_id=source.project_id,
        source_id=source.id,
        status=source.status,
        review_note=source.review_note,
    )


@router.get("/projects/{project_id}/brief", response_model=ResearchBrief)
def get_brief(project_id: str, session: Session = DbSession) -> ResearchBrief:
    project = sqlalchemy_research_store.get(session, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="research project not found",
        )

    return DeterministicBriefGenerator().generate(project)
