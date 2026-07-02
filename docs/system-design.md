# System Design

## 1. Goals

- Create research projects from natural-language questions.
- Collect sources with provenance and key claims.
- Score source credibility deterministically.
- Generate cited preliminary briefs from evidence cards.
- Prepare the architecture for future multi-agent search, verification, synthesis, critique, and citation workflows.

## 2. Non-Goals

- Calling paid search or model APIs in the initial implementation.
- Claiming final truth without human review.
- Replacing primary source reading.
- Storing private documents without explicit privacy controls.

## 3. Functional Requirements

- Create a research project.
- Add sources to a project.
- Deduplicate sources within a project by normalized URL or normalized title.
- Capture URL, title, source type, author, publication date, summary, and key claims.
- Review source status as candidate, verified, rejected, or needs_review with a short note.
- Score source credibility with transparent reasons.
- Generate a brief with answer text, evidence cards, average credibility, and research gaps while excluding rejected sources.

## 4. Non-Functional Requirements

- Local and CI behavior must be deterministic.
- Brief generation must be reproducible from stored sources.
- Credibility scoring must expose reasons, not just a number.
- The system must support future async agent execution.
- Outputs should clearly distinguish evidence from synthesis.

## 5. Data Model

Initial entities:

- `research_projects`: ID, question, created timestamp.
- `research_sources`: ID, project ID, title, normalized title, URL, normalized URL, source type, author, publication date, summary, key claims, review status, review note, reviewed timestamp, added timestamp.
- `credibility_assessments`: source ID, score, label, reasons, assessed timestamp.
- `research_briefs`: project ID, answer, evidence cards, gaps, generated timestamp.
- `agent_runs`: future workflow runs with role, status, attempts, input/output metadata, and timestamps.

The current implementation includes SQLAlchemy models and an Alembic migration for PostgreSQL. Local tests validate the same model behavior with SQLite.

## 6. API Design

Initial endpoints:

- `GET /health`: service health and environment.
- `POST /research/projects`: create a research project.
- `POST /research/projects/{project_id}/sources`: add or deduplicate a source and return credibility assessment.
- `PATCH /research/projects/{project_id}/sources/{source_id}/review`: update source review status and reviewer note.
- `GET /research/projects/{project_id}/brief`: generate a deterministic cited brief.

Planned endpoints:

- `POST /research/projects/{project_id}/agent-runs`: start a search/verify/synthesize workflow.
- `GET /research/projects/{project_id}/sources`: inspect source table.
- `GET /research/projects/{project_id}/exports/markdown`: export a cited brief.

## 7. Agent Workflow

1. Search agent proposes candidate sources.
2. Verifier agent checks source metadata and extracts key claims.
3. Verifier agent or human reviewer marks each source as verified, rejected, or needing more review.
4. Credibility scorer ranks usable sources and explains scoring reasons.
5. Synthesis agent drafts a brief from evidence cards, preferring verified sources and excluding rejected sources.
6. Critic agent flags gaps, weak evidence, unverified candidates, and overclaims.
7. Citation agent formats the final source map.

The first implementation covers steps 3 and 4 deterministically and leaves external search/model agents for later.

## 8. Scaling Strategy

- Use stateless API replicas.
- Store projects, sources, assessments, briefs, and agent runs in PostgreSQL.
- Use Redis workers for long-running source search and synthesis tasks.
- Cache generated briefs and invalidate them when sources change.
- Partition project data by user or workspace when authentication is added.

## 9. Reliability Strategy

- Persist source records before launching async verification or synthesis.
- Deduplicate source submissions before generating credibility assessments.
- Keep source review updates idempotent and preserve rejected sources for audit history.
- Make agent runs idempotent by project ID, role, and input hash.
- Store prompt/model/provider metadata for reproducibility.
- Keep deterministic fallback scoring available when external providers fail.
- Track failed agent runs with attempts and last error.

## 10. Observability

- Structured logs for project ID, source ID, agent role, status, and latency.
- Metrics for source intake, scoring latency, brief generation latency, and failed agent runs.
- Traces across API, database, queue, search providers, and model providers.
- Audit history for source changes and brief exports.

## 11. Security And Safety

- Keep provider keys out of source control.
- Treat user research notes and uploads as private data.
- Redact private content before external model calls where possible.
- Label generated briefs as preliminary.
- Preserve citations and evidence gaps to reduce unsupported conclusions.
- Exclude rejected sources from generated evidence while retaining review notes for traceability.

## 12. Tradeoffs

- Deterministic scoring is simple and reproducible, but it cannot fully judge source quality.
- SQLite-backed tests keep persistence behavior deterministic without requiring Docker.
- FastAPI keeps the service compact; a later frontend can consume the same API.
- Multi-agent orchestration is deferred until the core source/evidence model is stable.

## 13. Future Improvements

- Search provider connectors.
- Async multi-agent workflow engine.
- LLM synthesis constrained to evidence cards.
- Frontend research board and export workflow.
