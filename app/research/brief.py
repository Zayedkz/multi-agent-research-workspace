from statistics import mean

from app.research.credibility import DeterministicCredibilityScorer
from app.research.models import EvidenceCard, ResearchBrief, ResearchProject


class DeterministicBriefGenerator:
    def __init__(self, scorer: DeterministicCredibilityScorer | None = None) -> None:
        self.scorer = scorer or DeterministicCredibilityScorer()

    def generate(self, project: ResearchProject) -> ResearchBrief:
        assessments = {source.id: self.scorer.assess(source) for source in project.sources}
        evidence = [
            EvidenceCard(
                source_id=source.id,
                title=source.title,
                url=source.url,
                claim=claim,
                credibility_score=assessments[source.id].score,
            )
            for source in project.sources
            for claim in (source.key_claims or [source.summary])
        ]
        evidence.sort(key=lambda card: card.credibility_score, reverse=True)

        average_credibility = (
            round(mean(assessment.score for assessment in assessments.values()), 3)
            if assessments
            else 0.0
        )

        return ResearchBrief(
            project_id=project.id,
            question=project.question,
            source_count=len(project.sources),
            average_credibility=average_credibility,
            answer=self._answer(project, evidence),
            evidence=evidence[:8],
            gaps=self._gaps(project),
        )

    def _answer(self, project: ResearchProject, evidence: list[EvidenceCard]) -> str:
        if not evidence:
            return "No sources have been added yet, so there is not enough evidence for a brief."

        top_claims = "; ".join(card.claim for card in evidence[:3])
        return (
            f"Preliminary answer to '{project.question}': {top_claims}. "
            "Treat this as a cited research brief, not a final conclusion."
        )

    def _gaps(self, project: ResearchProject) -> list[str]:
        gaps: list[str] = []
        source_types = {source.source_type for source in project.sources}

        if len(project.sources) < 3:
            gaps.append(
                "Add at least three independent sources before treating the brief as strong."
            )
        if "academic" not in source_types and "government" not in source_types:
            gaps.append("Add at least one academic or government source for stronger grounding.")
        if any(not source.published_at for source in project.sources):
            gaps.append("Some sources are missing publication dates.")

        return gaps
