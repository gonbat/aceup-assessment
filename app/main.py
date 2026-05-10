from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse
import gradio as gr
from pydantic import ValidationError

from app.adapters.openai import OpenAIAdapter
from app.configurations import EnvConfigs
from app.mappers import to_batch_transcript_analysis_response, to_transcript_analysis_response
from app.schemas import (
    BatchTranscriptAnalysisRequest,
    BatchTranscriptAnalysisResponse,
    TranscriptAnalysisResponse,
)
from app.errors import (
    AnalysisNotFoundError,
    ConfigurationError,
    InvalidTranscriptError,
    LLMCompletionError,
)
from app.frontend import build_gradio_app
from app.ports import LLm
from app.repositories import InMemoryTranscriptAnalysisRepository, TranscriptAnalysisRepository
from app.services import TranscriptAnalysisService

app = FastAPI(
    title="Transcript Analysis API",
    version="0.1.0",
    description="Analyze plain text transcripts and retrieve stored analysis results.",
)

_repository = InMemoryTranscriptAnalysisRepository()


@lru_cache
def get_env_configs() -> EnvConfigs:
    try:
        return EnvConfigs()
    except ValidationError as exc:
        raise ConfigurationError(
            "OPENAI_API_KEY is not configured. Set it in .env or as an environment variable."
        ) from exc


@lru_cache
def get_llm() -> LLm:
    env_configs = get_env_configs()
    return OpenAIAdapter(env_configs.OPENAI_API_KEY, env_configs.OPENAI_MODEL)


def get_repository() -> TranscriptAnalysisRepository:
    return _repository


def get_analysis_service(
    llm: Annotated[LLm, Depends(get_llm)],
    repository: Annotated[TranscriptAnalysisRepository, Depends(get_repository)],
) -> TranscriptAnalysisService:
    return TranscriptAnalysisService(llm, repository)


def get_gradio_analysis_service() -> TranscriptAnalysisService:
    return TranscriptAnalysisService(get_llm(), get_repository())


@app.exception_handler(InvalidTranscriptError)
async def invalid_transcript_handler(_: Request, exc: InvalidTranscriptError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(AnalysisNotFoundError)
async def analysis_not_found_handler(_: Request, exc: AnalysisNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(_: Request, exc: ConfigurationError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(LLMCompletionError)
async def llm_completion_handler(_: Request, exc: LLMCompletionError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.get("/analyses", response_model=TranscriptAnalysisResponse)
def analyze_transcript(
    transcript: Annotated[str, Query(description="Plain text transcript to analyze.")],
    service: Annotated[TranscriptAnalysisService, Depends(get_analysis_service)],
) -> TranscriptAnalysisResponse:
    analysis = service.analyze(transcript)
    return to_transcript_analysis_response(analysis)


@app.get("/analyses/{analysis_id}", response_model=TranscriptAnalysisResponse)
def get_transcript_analysis(
    analysis_id: str,
    service: Annotated[TranscriptAnalysisService, Depends(get_analysis_service)],
) -> TranscriptAnalysisResponse:
    analysis = service.get(analysis_id)
    return to_transcript_analysis_response(analysis)


@app.post("/analyses/batch", response_model=BatchTranscriptAnalysisResponse)
async def analyze_transcripts_batch(
    request: BatchTranscriptAnalysisRequest,
    service: Annotated[TranscriptAnalysisService, Depends(get_analysis_service)],
) -> BatchTranscriptAnalysisResponse:
    analyses = await service.analyze_many(request.transcripts)
    return to_batch_transcript_analysis_response(analyses)


app = gr.mount_gradio_app(app, build_gradio_app(get_gradio_analysis_service), path="/")
