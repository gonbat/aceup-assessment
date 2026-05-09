from app.domain import TranscriptAnalysis
from app.schemas import BatchTranscriptAnalysisResponse, TranscriptAnalysisResponse


def to_transcript_analysis_response(analysis: TranscriptAnalysis) -> TranscriptAnalysisResponse:
    return TranscriptAnalysisResponse(
        id=analysis.id,
        summary=analysis.summary,
        action_items=list(analysis.action_items),
    )


def to_batch_transcript_analysis_response(
    analyses: list[TranscriptAnalysis],
) -> BatchTranscriptAnalysisResponse:
    return BatchTranscriptAnalysisResponse(
        items=[to_transcript_analysis_response(analysis) for analysis in analyses]
    )
