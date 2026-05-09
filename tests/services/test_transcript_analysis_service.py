import asyncio

import pydantic
import pytest

from app.errors import AnalysisNotFoundError, InvalidTranscriptError, LLMCompletionError
from app.ports import LLm
from app.repositories import InMemoryTranscriptAnalysisRepository
from app.services import TranscriptAnalysisService


class FakeLLM(LLm):
    def __init__(self) -> None:
        self.user_prompts: list[str] = []
        self.async_user_prompts: list[str] = []

    def run_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[pydantic.BaseModel],
    ) -> pydantic.BaseModel:
        self.user_prompts.append(user_prompt)
        return dto(summary="A concise summary.", action_items=["Follow up", "Share notes"])

    async def run_completion_async(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[pydantic.BaseModel],
    ) -> pydantic.BaseModel:
        self.async_user_prompts.append(user_prompt)
        return dto(summary="A concise summary.", action_items=["Follow up", "Share notes"])


class FailingLLM(LLm):
    def run_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[pydantic.BaseModel],
    ) -> pydantic.BaseModel:
        raise RuntimeError("provider unavailable")

    async def run_completion_async(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[pydantic.BaseModel],
    ) -> pydantic.BaseModel:
        raise RuntimeError("provider unavailable")


def build_service(llm: LLm | None = None) -> TranscriptAnalysisService:
    return TranscriptAnalysisService(llm or FakeLLM(), InMemoryTranscriptAnalysisRepository())


def test_analyze_returns_and_persists_result() -> None:
    llm = FakeLLM()
    service = build_service(llm)

    analysis = service.analyze("  Discuss launch plan.  ")

    assert analysis.id
    assert analysis.summary == "A concise summary."
    assert analysis.action_items == ("Follow up", "Share notes")
    assert service.get(analysis.id) == analysis
    assert "Discuss launch plan." in llm.user_prompts[0]


def test_analyze_rejects_empty_transcript() -> None:
    service = build_service()

    with pytest.raises(InvalidTranscriptError):
        service.analyze("   ")


def test_get_raises_when_analysis_is_missing() -> None:
    service = build_service()

    with pytest.raises(AnalysisNotFoundError):
        service.get("missing-id")


def test_analyze_many_processes_and_persists_all_results() -> None:
    llm = FakeLLM()
    service = build_service(llm)

    analyses = asyncio.run(service.analyze_many(["First transcript", "Second transcript"]))

    assert len(analyses) == 2
    assert len({analysis.id for analysis in analyses}) == 2
    assert [service.get(analysis.id) for analysis in analyses] == analyses
    assert len(llm.async_user_prompts) == 2
    assert llm.user_prompts == []


def test_analyze_many_rejects_empty_list() -> None:
    service = build_service()

    with pytest.raises(InvalidTranscriptError):
        asyncio.run(service.analyze_many([]))


def test_llm_errors_are_wrapped() -> None:
    service = build_service(FailingLLM())

    with pytest.raises(LLMCompletionError):
        service.analyze("Discuss launch plan.")


def test_analyze_many_wraps_llm_errors() -> None:
    service = build_service(FailingLLM())

    with pytest.raises(LLMCompletionError):
        asyncio.run(service.analyze_many(["Discuss launch plan."]))
