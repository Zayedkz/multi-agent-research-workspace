from datetime import UTC, datetime

from app.research.brief import DeterministicBriefGenerator
from app.research.models import ResearchProject, ResearchSource, SourceStatus, SourceType


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


def test_brief_excludes_rejected_sources() -> None:
    project = ResearchProject(
        id="project-rejected",
        question="What should be included?",
        sources=[
            ResearchSource(
                id="rejected-source",
                project_id="project-rejected",
                title="Rejected claim",
                url="https://example.com/rejected",
                source_type=SourceType.government,
                summary="This should not appear.",
                key_claims=["Rejected evidence should be excluded."],
                status=SourceStatus.rejected,
            ),
            ResearchSource(
                id="candidate-source",
                project_id="project-rejected",
                title="Candidate claim",
                url="https://example.com/candidate",
                source_type=SourceType.news,
                summary="This should appear.",
                key_claims=["Candidate evidence can be used with warnings."],
            ),
        ],
    )

    brief = DeterministicBriefGenerator().generate(project)

    assert brief.source_count == 1
    assert [card.source_id for card in brief.evidence] == ["candidate-source"]
    assert "Rejected evidence" not in brief.answer


def test_brief_prioritizes_verified_sources_over_higher_scoring_candidates() -> None:
    project = ResearchProject(
        id="project-verified",
        question="Which source should lead?",
        sources=[
            ResearchSource(
                id="candidate-high",
                project_id="project-verified",
                title="Candidate government source",
                url="https://example.gov/candidate",
                source_type=SourceType.government,
                author="Agency",
                published_at=datetime(2026, 1, 1, tzinfo=UTC),
                summary="A high-credibility candidate.",
                key_claims=["Candidate source has strong metadata."],
            ),
            ResearchSource(
                id="verified-lower",
                project_id="project-verified",
                title="Verified blog source",
                url="https://example.com/verified",
                source_type=SourceType.blog,
                summary="A reviewed but lower scoring source.",
                key_claims=["Verified source was reviewed by a human."],
                status=SourceStatus.verified,
                review_note="Relevant and fact checked.",
            ),
        ],
    )

    brief = DeterministicBriefGenerator().generate(project)

    assert brief.evidence[0].source_id == "verified-lower"
    assert "Verified source was reviewed" in brief.answer


def test_candidate_only_low_credibility_brief_reports_review_gap() -> None:
    project = ResearchProject(
        id="project-gap",
        question="Is this well supported?",
        sources=[
            ResearchSource(
                id="social-candidate",
                project_id="project-gap",
                title="Social post",
                url="https://example.com/social",
                source_type=SourceType.social,
                summary="Anecdotal discussion.",
                key_claims=["Anecdotal source claims support."],
            ),
        ],
    )

    brief = DeterministicBriefGenerator().generate(project)

    assert any("No sources have been verified yet" in gap for gap in brief.gaps)
    assert any("Available sources are low credibility" in gap for gap in brief.gaps)
