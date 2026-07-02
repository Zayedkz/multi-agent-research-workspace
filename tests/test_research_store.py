from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.research.models import ResearchSource, SourceStatus, SourceType
from app.research.store import normalize_title, normalize_url, sqlalchemy_research_store


def test_sqlalchemy_store_persists_project_and_source(db_session: Session) -> None:
    project = sqlalchemy_research_store.create_project(
        db_session,
        "What makes research workflows reliable?",
    )
    source = ResearchSource(
        project_id=project.id,
        title="Government Guidance",
        url="https://example.gov/guidance?utm_source=newsletter",
        source_type=SourceType.government,
        author="Research Office",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        summary="Guidance summary.",
        key_claims=["Evidence should be traceable."],
    )

    result = sqlalchemy_research_store.add_source(db_session, source)
    loaded = sqlalchemy_research_store.get(db_session, project.id)

    assert result.created is True
    assert loaded is not None
    assert loaded.question == "What makes research workflows reliable?"
    assert len(loaded.sources) == 1
    assert loaded.sources[0].key_claims == ["Evidence should be traceable."]
    assert loaded.sources[0].status == SourceStatus.candidate


def test_sqlalchemy_store_updates_source_review_status(db_session: Session) -> None:
    project = sqlalchemy_research_store.create_project(db_session, "Question?")
    created = sqlalchemy_research_store.add_source(
        db_session,
        ResearchSource(
            project_id=project.id,
            title="Reviewable Source",
            url="https://example.com/reviewable",
            source_type=SourceType.news,
            summary="This source needs a reviewer decision.",
        ),
    )

    reviewed = sqlalchemy_research_store.update_source_status(
        db_session,
        project.id,
        created.source.id,
        SourceStatus.needs_review,
        "Author is unclear.",
    )
    loaded = sqlalchemy_research_store.get(db_session, project.id)

    assert reviewed is not None
    assert reviewed.status == SourceStatus.needs_review
    assert reviewed.review_note == "Author is unclear."
    assert reviewed.reviewed_at is not None
    assert loaded is not None
    assert loaded.sources[0].status == SourceStatus.needs_review


def test_sqlalchemy_store_deduplicates_sources_by_normalized_url(db_session: Session) -> None:
    project = sqlalchemy_research_store.create_project(db_session, "Question?")
    first = ResearchSource(
        project_id=project.id,
        title="Original Title",
        url="https://example.com/article?utm_campaign=x&b=2&a=1",
        source_type=SourceType.news,
        summary="First summary.",
    )
    second = ResearchSource(
        project_id=project.id,
        title="Different Title",
        url="https://EXAMPLE.com/article/?a=1&b=2",
        source_type=SourceType.blog,
        summary="Second summary.",
    )

    created = sqlalchemy_research_store.add_source(db_session, first)
    duplicate = sqlalchemy_research_store.add_source(db_session, second)

    assert created.created is True
    assert duplicate.created is False
    assert duplicate.source.id == created.source.id
    assert len(duplicate.project.sources) == 1


def test_sqlalchemy_store_deduplicates_sources_by_normalized_title(db_session: Session) -> None:
    project = sqlalchemy_research_store.create_project(db_session, "Question?")
    first = ResearchSource(
        project_id=project.id,
        title="  Evidence Quality Guide ",
        url="https://example.com/one",
        source_type=SourceType.blog,
        summary="First summary.",
    )
    second = ResearchSource(
        project_id=project.id,
        title="evidence   quality guide",
        url="https://example.com/two",
        source_type=SourceType.blog,
        summary="Second summary.",
    )

    created = sqlalchemy_research_store.add_source(db_session, first)
    duplicate = sqlalchemy_research_store.add_source(db_session, second)

    assert created.created is True
    assert duplicate.created is False
    assert duplicate.source.id == created.source.id
    assert len(duplicate.project.sources) == 1


def test_normalizers_remove_tracking_query_and_case_noise() -> None:
    assert normalize_title("  My   Source TITLE ") == "my source title"
    assert (
        normalize_url("HTTPS://Example.COM/path/?utm_source=x&b=2&a=1#section")
        == "https://example.com/path?a=1&b=2"
    )
