from typing import Self

from pydantic import BaseModel

from app.domain import TranscriptAnalysis


class LLMTranscriptAnalysisResponse(BaseModel):
    summary: str
    action_items: list[str]


class TranscriptAnalysisResponse(BaseModel):
    id: str
    summary: str
    action_items: list[str]

    @classmethod
    def from_domain(cls, analysis: TranscriptAnalysis) -> Self:
        return cls(
            id=analysis.id,
            summary=analysis.summary,
            action_items=list(analysis.action_items),
        )


class BatchTranscriptAnalysisRequest(BaseModel):
    transcripts: list[str]


class BatchTranscriptAnalysisResponse(BaseModel):
    items: list[TranscriptAnalysisResponse]

    @classmethod
    def from_domain(cls, analyses: list[TranscriptAnalysis]) -> Self:
        return cls(items=[TranscriptAnalysisResponse.from_domain(analysis) for analysis in analyses])
