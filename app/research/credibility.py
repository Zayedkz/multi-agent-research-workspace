from datetime import UTC, datetime

from app.research.models import CredibilityAssessment, ResearchSource, SourceType


class DeterministicCredibilityScorer:
    def assess(self, source: ResearchSource) -> CredibilityAssessment:
        score = 0.35
        reasons: list[str] = []

        type_weight = {
            SourceType.academic: 0.3,
            SourceType.government: 0.28,
            SourceType.news: 0.18,
            SourceType.company: 0.12,
            SourceType.blog: 0.08,
            SourceType.social: 0.02,
            SourceType.unknown: 0.0,
        }[source.source_type]
        score += type_weight
        reasons.append(f"{source.source_type} source type contributes {type_weight:.2f}.")

        if source.author:
            score += 0.08
            reasons.append("Named author improves accountability.")

        if source.published_at:
            published_at = source.published_at
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=UTC)
            age_days = (datetime.now(UTC) - published_at).days
            if age_days <= 730:
                score += 0.12
                reasons.append("Recent publication improves current relevance.")
            else:
                score += 0.04
                reasons.append("Older publication may still be useful but needs context.")
        else:
            reasons.append("Missing publication date reduces freshness confidence.")

        if len(source.key_claims) >= 2:
            score += 0.1
            reasons.append("Multiple explicit claims make the source easier to audit.")

        score = round(min(score, 1.0), 3)
        return CredibilityAssessment(
            source_id=source.id,
            score=score,
            label=self._label(score),
            reasons=reasons,
        )

    def _label(self, score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.55:
            return "medium"
        return "low"
