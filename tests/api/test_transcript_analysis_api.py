import pydantic
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_analysis_service
from app.ports import LLm
from app.repositories import InMemoryTranscriptAnalysisRepository
from app.services import TranscriptAnalysisService


class FakeLLM(LLm):
    def run_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[pydantic.BaseModel],
    ) -> pydantic.BaseModel:
        return dto(summary="API summary.", action_items=["Confirm owner", "Set deadline"])


@pytest.fixture
def client() -> TestClient:
    service = TranscriptAnalysisService(FakeLLM(), InMemoryTranscriptAnalysisRepository())
    app.dependency_overrides[get_analysis_service] = lambda: service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_analyze_transcript_success(client: TestClient) -> None:
    response = client.get("/analyses", params={"transcript": "Discuss rollout plan."})

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"]
    assert payload["summary"] == "API summary."
    assert payload["action_items"] == ["Confirm owner", "Set deadline"]


def test_analyze_transcript_rejects_empty_query(client: TestClient) -> None:
    response = client.get("/analyses", params={"transcript": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Transcript cannot be empty."


def test_get_transcript_analysis_success(client: TestClient) -> None:
    created = client.get("/analyses", params={"transcript": "Discuss rollout plan."}).json()

    response = client.get(f"/analyses/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_transcript_analysis_returns_404(client: TestClient) -> None:
    response = client.get("/analyses/missing-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transcript analysis 'missing-id' was not found."


def test_analyze_batch_success(client: TestClient) -> None:
    response = client.post(
        "/analyses/batch",
        json={"transcripts": ["Discuss roadmap.", "Review hiring plan."]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert all(item["summary"] == "API summary." for item in payload["items"])


def test_analyze_batch_rejects_empty_list(client: TestClient) -> None:
    response = client.post("/analyses/batch", json={"transcripts": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one transcript is required."


def test_analyze_batch_rejects_empty_transcript(client: TestClient) -> None:
    response = client.post("/analyses/batch", json={"transcripts": ["Discuss roadmap.", "  "]})

    assert response.status_code == 400
    assert response.json()["detail"] == "Transcript cannot be empty."


def test_gradio_ui_is_mounted(client: TestClient) -> None:
    response = client.get("/ui/", follow_redirects=True)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
