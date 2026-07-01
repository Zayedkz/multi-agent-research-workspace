from fastapi.testclient import TestClient

from app.main import app


def test_research_project_source_and_brief_flow(app_with_test_db: None) -> None:
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
    assert source.json()["created"] is True
    assert source.json()["credibility"]["label"] == "high"
    assert brief.status_code == 200
    body = brief.json()
    assert body["source_count"] == 1
    assert body["evidence"][0]["title"] == "Research workflow guidance"
    assert "evidence provenance" in body["answer"]


def test_duplicate_source_returns_existing_source(app_with_test_db: None) -> None:
    client = TestClient(app)
    project_id = client.post(
        "/research/projects",
        json={"question": "How do we track evidence?"},
    ).json()["project_id"]
    payload = {
        "title": "Evidence Tracking",
        "url": "https://example.com/evidence?utm_source=feed",
        "source_type": "blog",
        "summary": "Evidence should be traceable.",
    }

    first = client.post(f"/research/projects/{project_id}/sources", json=payload)
    second = client.post(
        f"/research/projects/{project_id}/sources",
        json={**payload, "url": "https://example.com/evidence/"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert first.json()["source_id"] == second.json()["source_id"]
    assert second.json()["source_count"] == 1


def test_missing_project_brief_returns_404(app_with_test_db: None) -> None:
    response = TestClient(app).get("/research/projects/missing/brief")

    assert response.status_code == 404
