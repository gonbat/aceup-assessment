from pydantic import BaseModel


class TranscriptAnalysisResponse(BaseModel):
    id: str
    summary: str
    action_items: list[str]


class BatchTranscriptAnalysisRequest(BaseModel):
    transcripts: list[str]


class BatchTranscriptAnalysisResponse(BaseModel):
    items: list[TranscriptAnalysisResponse]
