import asyncio
import uuid
from collections.abc import Sequence

import pydantic

from app import prompts
from app.domain import TranscriptAnalysis
from app.dtos import LLMTranscriptAnalysisResponse
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
            *(asyncio.to_thread(self._create_analysis, transcript) for transcript in clean_transcripts)
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

        try:
            if isinstance(completion, pydantic.BaseModel):
                return LLMTranscriptAnalysisResponse.model_validate(completion.model_dump())
            return LLMTranscriptAnalysisResponse.model_validate(completion)
        except pydantic.ValidationError as exc:
            raise LLMCompletionError("Transcript analysis returned an invalid response.") from exc

    @staticmethod
    def _validate_transcript(transcript: str) -> str:
        clean_transcript = transcript.strip()
        if not clean_transcript:
            raise InvalidTranscriptError("Transcript cannot be empty.")
        return clean_transcript
