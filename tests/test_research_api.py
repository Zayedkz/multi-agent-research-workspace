from fastapi.testclient import TestClient

from app.main import app


def test_research_project_source_and_brief_flow() -> None:
    client = TestClient(app)
    created = client.post(
        "/research/projects",
        json={"question": "What makes multi-agent research workflows reliable?"},
    )
    project_id = created.json()["project_id"]

    source = client.post(
        f"/research/projects/{project_id}/sources",
        json={
            "title": "Research workflow guidance",
            "url": "https://example.gov/research-guidance",
            "source_type": "government",
            "author": "Research Office",
            "published_at": "2026-01-01T00:00:00Z",
            "summary": "Guidance on auditable research workflows.",
            "key_claims": [
                "Reliable research workflows track evidence provenance.",
                "Credibility scoring helps reviewers compare sources.",
            ],
        },
    )
    brief = client.get(f"/research/projects/{project_id}/brief")

    assert created.status_code == 201
    assert source.status_code == 201
    assert source.json()["credibility"]["label"] == "high"
    assert brief.status_code == 200
    body = brief.json()
    assert body["source_count"] == 1
    assert body["evidence"][0]["title"] == "Research workflow guidance"
    assert "evidence provenance" in body["answer"]


def test_missing_project_brief_returns_404() -> None:
    response = TestClient(app).get("/research/projects/missing/brief")

    assert response.status_code == 404
