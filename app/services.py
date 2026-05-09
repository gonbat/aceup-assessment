import asyncio
import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ValidationError

from app import prompts
from app.domain import TranscriptAnalysis
from app.llm_schema import LLMTranscriptAnalysisResponse
from app.errors import AnalysisNotFoundError, InvalidTranscriptError, LLMCompletionError
from app.ports import LLm
from app.repositories import TranscriptAnalysisRepository


class TranscriptAnalysisService:
    def __init__(self, llm: LLm, repository: TranscriptAnalysisRepository) -> None:
        self._llm = llm
        self._repository = repository

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        clean_transcript = self._validate_transcript(transcript)
        analysis = self._create_analysis(clean_transcript)
        self._repository.save(analysis)
        return analysis

    async def analyze_many(self, transcripts: Sequence[str]) -> list[TranscriptAnalysis]:
        if not transcripts:
            raise InvalidTranscriptError("At least one transcript is required.")

        clean_transcripts = [self._validate_transcript(transcript) for transcript in transcripts]
        analyses = await asyncio.gather(
            *(self._create_analysis_async(transcript) for transcript in clean_transcripts)
        )

        for analysis in analyses:
            self._repository.save(analysis)

        return list(analyses)

    def get(self, analysis_id: str) -> TranscriptAnalysis:
        analysis = self._repository.get(analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError(f"Transcript analysis '{analysis_id}' was not found.")
        return analysis

    def _create_analysis(self, transcript: str) -> TranscriptAnalysis:
        response = self._run_completion(transcript)
        return self._build_analysis(response)

    async def _create_analysis_async(self, transcript: str) -> TranscriptAnalysis:
        response = await self._run_completion_async(transcript)
        return self._build_analysis(response)

    @staticmethod
    def _build_analysis(response: LLMTranscriptAnalysisResponse) -> TranscriptAnalysis:
        return TranscriptAnalysis(
            id=str(uuid.uuid4()),
            summary=response.summary,
            action_items=tuple(response.action_items),
        )

    def _run_completion(self, transcript: str) -> LLMTranscriptAnalysisResponse:
        user_prompt = prompts.RAW_USER_PROMPT.format(transcript=transcript)

        try:
            completion = self._llm.run_completion(
                prompts.SYSTEM_PROMPT,
                user_prompt,
                LLMTranscriptAnalysisResponse,
            )
        except Exception as exc:
            raise LLMCompletionError("Transcript analysis failed.") from exc

        return self._parse_completion_response(completion)

    async def _run_completion_async(self, transcript: str) -> LLMTranscriptAnalysisResponse:
        user_prompt = prompts.RAW_USER_PROMPT.format(transcript=transcript)

        try:
            completion = await self._llm.run_completion_async(
                prompts.SYSTEM_PROMPT,
                user_prompt,
                LLMTranscriptAnalysisResponse,
            )
        except Exception as exc:
            raise LLMCompletionError("Transcript analysis failed.") from exc

        return self._parse_completion_response(completion)

    @staticmethod
    def _parse_completion_response(completion: BaseModel | object) -> LLMTranscriptAnalysisResponse:
        try:
            if isinstance(completion, BaseModel):
                return LLMTranscriptAnalysisResponse.model_validate(completion.model_dump())
            return LLMTranscriptAnalysisResponse.model_validate(completion)
        except ValidationError as exc:
            raise LLMCompletionError("Transcript analysis returned an invalid response.") from exc

    @staticmethod
    def _validate_transcript(transcript: str) -> str:
        clean_transcript = transcript.strip()
        if not clean_transcript:
            raise InvalidTranscriptError("Transcript cannot be empty.")
        return clean_transcript
