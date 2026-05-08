import gradio as gr
import pytest

from app.domain import TranscriptAnalysis
from app.errors import AnalysisNotFoundError, InvalidTranscriptError
from app.frontend import analyze_transcript, format_action_items, lookup_analysis


class FakeService:
    def __init__(self) -> None:
        self.analysis = TranscriptAnalysis(
            id="analysis-1",
            summary="The team aligned on next steps.",
            action_items=("Confirm owner", "Set deadline"),
        )

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        if not transcript.strip():
            raise InvalidTranscriptError("Transcript cannot be empty.")
        return self.analysis

    def get(self, analysis_id: str) -> TranscriptAnalysis:
        if analysis_id != self.analysis.id:
            raise AnalysisNotFoundError(f"Transcript analysis '{analysis_id}' was not found.")
        return self.analysis


def test_analyze_transcript_returns_formatted_result() -> None:
    result = analyze_transcript("Discuss roadmap.", FakeService)

    assert result == (
        "analysis-1",
        "The team aligned on next steps.",
        "1. Confirm owner\n2. Set deadline",
    )


def test_lookup_analysis_returns_formatted_result() -> None:
    result = lookup_analysis(" analysis-1 ", FakeService)

    assert result == (
        "analysis-1",
        "The team aligned on next steps.",
        "1. Confirm owner\n2. Set deadline",
    )


def test_analyze_transcript_maps_empty_input_to_gradio_error() -> None:
    with pytest.raises(gr.Error, match="Transcript cannot be empty."):
        analyze_transcript("   ", FakeService)


def test_lookup_analysis_maps_missing_id_to_gradio_error() -> None:
    with pytest.raises(gr.Error, match="Transcript analysis 'missing-id' was not found."):
        lookup_analysis("missing-id", FakeService)


def test_format_action_items_handles_empty_list() -> None:
    assert format_action_items(()) == "No suggested next steps returned."
