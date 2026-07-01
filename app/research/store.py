from app.research.models import ResearchProject, ResearchSource


class ResearchStore:
    def create_project(self, question: str) -> ResearchProject:
        raise NotImplementedError

    def add_source(self, source: ResearchSource) -> ResearchProject:
        raise NotImplementedError

    def get(self, project_id: str) -> ResearchProject | None:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError


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


research_store = InMemoryResearchStore()
