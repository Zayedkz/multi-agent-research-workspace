from datetime import UTC, datetime

from app.research.credibility import DeterministicCredibilityScorer
from app.research.models import ResearchSource, SourceType


def test_academic_source_with_author_claims_and_recent_date_scores_high() -> None:
    source = ResearchSource(
        project_id="project-1",
        title="Peer reviewed AI study",
        url="https://example.edu/paper",
        source_type=SourceType.academic,
        author="Dr. Researcher",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        summary="A peer reviewed study.",
        key_claims=["Claim one.", "Claim two."],
    )

    assessment = DeterministicCredibilityScorer().assess(source)

    assert assessment.label == "high"
    assert assessment.score >= 0.75
    assert any("Named author" in reason for reason in assessment.reasons)


def test_social_source_without_date_scores_low() -> None:
    source = ResearchSource(
        project_id="project-1",
        title="Social post",
        url="https://example.com/post",
        source_type=SourceType.social,
        summary="A short uncited claim.",
    )

    assessment = DeterministicCredibilityScorer().assess(source)

    assert assessment.label == "low"
    assert assessment.score < 0.55
