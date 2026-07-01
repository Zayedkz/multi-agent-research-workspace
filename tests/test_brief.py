from datetime import UTC, datetime

from app.research.brief import DeterministicBriefGenerator
from app.research.models import ResearchProject, ResearchSource, SourceType


def test_brief_orders_evidence_by_credibility_and_reports_gaps() -> None:
    project = ResearchProject(
        id="project-1",
        question="How should teams evaluate AI research tools?",
        sources=[
            ResearchSource(
                id="source-low",
                project_id="project-1",
                title="Forum claim",
                url="https://example.com/forum",
                source_type=SourceType.social,
                summary="Anecdotal report.",
                key_claims=["Anecdotal tools are popular."],
            ),
            ResearchSource(
                id="source-high",
                project_id="project-1",
                title="Government guidance",
                url="https://example.gov/guidance",
                source_type=SourceType.government,
                author="Public agency",
                published_at=datetime(2026, 1, 1, tzinfo=UTC),
                summary="Official guidance.",
                key_claims=["Evaluate tools using evidence quality and repeatable workflows."],
            ),
        ],
    )

    brief = DeterministicBriefGenerator().generate(project)

    assert brief.source_count == 2
    assert brief.evidence[0].source_id == "source-high"
    assert "evidence quality" in brief.answer
    assert "Add at least three independent sources" in brief.gaps[0]


def test_empty_project_brief_has_no_evidence() -> None:
    project = ResearchProject(id="project-empty", question="What is known?")

    brief = DeterministicBriefGenerator().generate(project)

    assert brief.source_count == 0
    assert brief.average_credibility == 0
    assert brief.evidence == []
    assert "No sources" in brief.answer
