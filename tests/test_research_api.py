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
    assert source.json()["status"] == "candidate"
    assert source.json()["credibility"]["label"] == "high"
    assert brief.status_code == 200
    body = brief.json()
    assert body["source_count"] == 1
    assert body["evidence"][0]["title"] == "Research workflow guidance"
    assert "evidence provenance" in body["answer"]


def test_source_review_endpoint_updates_status_and_note(app_with_test_db: None) -> None:
    client = TestClient(app)
    project_id = client.post(
        "/research/projects",
        json={"question": "Which sources are ready for synthesis?"},
    ).json()["project_id"]
    source_id = client.post(
        f"/research/projects/{project_id}/sources",
        json={
            "title": "Primary guidance",
            "url": "https://example.gov/primary-guidance",
            "source_type": "government",
            "summary": "Official guidance for reviewed sources.",
        },
    ).json()["source_id"]

    response = client.patch(
        f"/research/projects/{project_id}/sources/{source_id}/review",
        json={
            "status": "verified",
            "review_note": "Matches the research question and has clear provenance.",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "project_id": project_id,
        "source_id": source_id,
        "status": "verified",
        "review_note": "Matches the research question and has clear provenance.",
    }


def test_missing_source_review_returns_404(app_with_test_db: None) -> None:
    response = TestClient(app).patch(
        "/research/projects/project-missing/sources/source-missing/review",
        json={"status": "rejected", "review_note": "Not relevant."},
    )

    assert response.status_code == 404


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
