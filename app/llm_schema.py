from pydantic import BaseModel


class LLMTranscriptAnalysisResponse(BaseModel):
    summary: str
    action_items: list[str]
