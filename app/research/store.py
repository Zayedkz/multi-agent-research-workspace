from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import ResearchProjectRecord, ResearchSourceRecord
from app.research.models import ResearchProject, ResearchSource, SourceType


class ResearchStore:
    def create_project(self, question: str) -> ResearchProject:
        raise NotImplementedError

    def add_source(self, source: ResearchSource) -> ResearchProject:
        raise NotImplementedError

    def get(self, project_id: str) -> ResearchProject | None:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError


class AddSourceResult:
    def __init__(self, project: ResearchProject, source: ResearchSource, created: bool) -> None:
        self.project = project
        self.source = source
        self.created = created


class InMemoryResearchStore(ResearchStore):
    def __init__(self) -> None:
        self._projects: dict[str, ResearchProject] = {}

    def create_project(self, question: str) -> ResearchProject:
        project = ResearchProject(question=question)
        self._projects[project.id] = project
        return project

    def add_source(self, source: ResearchSource) -> ResearchProject:
        project = self._projects.get(source.project_id)
        if project is None:
            project = ResearchProject(
                id=source.project_id,
                question=f"Research {source.project_id}",
            )
            self._projects[source.project_id] = project

        project.sources.append(source)
        return project

    def get(self, project_id: str) -> ResearchProject | None:
        return self._projects.get(project_id)

    def count(self) -> int:
        return len(self._projects)


class SqlAlchemyResearchStore(ResearchStore):
    def create_project(self, session: Session, question: str) -> ResearchProject:
        record = ResearchProjectRecord(question=question)
        session.add(record)
        session.commit()
        session.refresh(record)
        return project_from_record(record)

    def add_source(self, session: Session, source: ResearchSource) -> AddSourceResult:
        project = session.scalar(
            select(ResearchProjectRecord)
            .options(selectinload(ResearchProjectRecord.sources))
            .where(ResearchProjectRecord.id == source.project_id)
        )
        if project is None:
            project = ResearchProjectRecord(
                id=source.project_id,
                question=f"Research {source.project_id}",
            )
            session.add(project)
            session.flush()

        normalized_url = normalize_url(str(source.url))
        normalized_title = normalize_title(source.title)
        existing = session.scalar(
            select(ResearchSourceRecord)
            .where(ResearchSourceRecord.project_id == source.project_id)
            .where(
                (ResearchSourceRecord.normalized_url == normalized_url)
                | (ResearchSourceRecord.normalized_title == normalized_title)
            )
        )
        if existing is not None:
            session.commit()
            session.refresh(project)
            return AddSourceResult(
                project=project_from_record(project),
                source=source_from_record(existing),
                created=False,
            )

        record = ResearchSourceRecord(
            id=source.id,
            project_id=source.project_id,
            title=source.title,
            normalized_title=normalized_title,
            url=str(source.url),
            normalized_url=normalized_url,
            source_type=source.source_type.value,
            author=source.author,
            published_at=source.published_at,
            summary=source.summary,
            key_claims=source.key_claims,
            added_at=source.added_at,
        )
        session.add(record)
        session.commit()
        session.refresh(project)
        return AddSourceResult(
            project=project_from_record(project),
            source=source_from_record(record),
            created=True,
        )

    def get(self, session: Session, project_id: str) -> ResearchProject | None:
        record = session.scalar(
            select(ResearchProjectRecord)
            .options(selectinload(ResearchProjectRecord.sources))
            .where(ResearchProjectRecord.id == project_id)
        )
        if record is None:
            return None
        return project_from_record(record)

    def count(self, session: Session) -> int:
        return len(session.scalars(select(ResearchProjectRecord.id)).all())


def project_from_record(record: ResearchProjectRecord) -> ResearchProject:
    return ResearchProject(
        id=record.id,
        question=record.question,
        created_at=record.created_at,
        sources=[source_from_record(source) for source in record.sources],
    )


def source_from_record(record: ResearchSourceRecord) -> ResearchSource:
    return ResearchSource(
        id=record.id,
        project_id=record.project_id,
        title=record.title,
        url=record.url,
        source_type=SourceType(record.source_type),
        author=record.author,
        published_at=record.published_at,
        summary=record.summary,
        key_claims=record.key_claims,
        added_at=record.added_at,
    )


def normalize_title(title: str) -> str:
    return " ".join(title.casefold().strip().split())


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    hostname = (parts.hostname or "").lower()
    netloc = hostname
    if parts.port:
        netloc = f"{hostname}:{parts.port}"

    path = parts.path.rstrip("/") or "/"
    query_items = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    query = urlencode(sorted(query_items))
    return urlunsplit((scheme, netloc, path, query, ""))


research_store = InMemoryResearchStore()
sqlalchemy_research_store = SqlAlchemyResearchStore()
