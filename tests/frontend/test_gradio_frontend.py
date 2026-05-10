import gradio as gr
import pytest

from app.domain import TranscriptAnalysis
from app.errors import AnalysisNotFoundError, ConfigurationError, InvalidTranscriptError
from app.frontend import (
    analyze_transcript,
    analyze_transcript_for_ui,
    format_action_items,
    format_status_html,
    hide_lookup_loading,
    lookup_analysis,
    lookup_analysis_for_ui,
    show_analyze_failure,
    show_analyze_loading,
)


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


class MisconfiguredService:
    def analyze(self, transcript: str) -> TranscriptAnalysis:
        raise ConfigurationError("OPENAI_API_KEY is not configured.")

    def get(self, analysis_id: str) -> TranscriptAnalysis:
        raise ConfigurationError("OPENAI_API_KEY is not configured.")


def test_analyze_transcript_returns_formatted_result() -> None:
    result = analyze_transcript("Discuss roadmap.", FakeService)

    assert result == (
        "analysis-1",
        "The team aligned on next steps.",
        "1. Confirm owner\n2. Set deadline",
    )


def test_analyze_transcript_for_ui_reveals_result_group() -> None:
    result_visibility, result_markdown = analyze_transcript_for_ui(
        "Discuss roadmap.",
        FakeService,
    )

    assert result_visibility["visible"] is True
    assert "### Analysis ID\n`analysis-1`" in result_markdown
    assert "### Summary\nThe team aligned on next steps." in result_markdown
    assert "### Suggested Next Steps\n1. Confirm owner\n2. Set deadline" in result_markdown


def test_lookup_analysis_returns_formatted_result() -> None:
    result = lookup_analysis(" analysis-1 ", FakeService)

    assert result == (
        "analysis-1",
        "The team aligned on next steps.",
        "1. Confirm owner\n2. Set deadline",
    )


def test_show_analyze_loading_sets_status_and_hides_results() -> None:
    status_visibility, result_visibility, result_markdown, button_state = show_analyze_loading()

    assert status_visibility["visible"] is True
    assert "Analyzing transcript..." in status_visibility["value"]
    assert result_visibility["visible"] is False
    assert result_markdown == ""
    assert button_state["value"] == "Analyzing..."
    assert button_state["interactive"] is False


def test_lookup_analysis_for_ui_reveals_result_group() -> None:
    result_visibility, result_markdown = lookup_analysis_for_ui(" analysis-1 ", FakeService)

    assert result_visibility["visible"] is True
    assert "### Analysis ID\n`analysis-1`" in result_markdown
    assert "### Summary\nThe team aligned on next steps." in result_markdown
    assert "### Suggested Next Steps\n1. Confirm owner\n2. Set deadline" in result_markdown


def test_hide_lookup_loading_clears_status_and_restores_button() -> None:
    status_visibility, button_state = hide_lookup_loading()

    assert status_visibility["visible"] is False
    assert status_visibility["value"] == ""
    assert button_state["value"] == "Lookup"
    assert button_state["interactive"] is True


def test_show_analyze_failure_sets_error_status_and_restores_button() -> None:
    status_visibility, result_visibility, result_markdown, button_state = show_analyze_failure()

    assert status_visibility["visible"] is True
    assert "Could not complete the request." in status_visibility["value"]
    assert result_visibility["visible"] is False
    assert result_markdown == ""
    assert button_state["value"] == "Analyze"
    assert button_state["interactive"] is True


def test_format_status_html_escapes_message() -> None:
    status_html = format_status_html("<script>alert('x')</script>")

    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in status_html
    assert "<script>" not in status_html


def test_analyze_transcript_maps_empty_input_to_gradio_error() -> None:
    with pytest.raises(gr.Error, match="Transcript cannot be empty."):
        analyze_transcript("   ", FakeService)


def test_lookup_analysis_maps_missing_id_to_gradio_error() -> None:
    with pytest.raises(gr.Error, match="Transcript analysis 'missing-id' was not found."):
        lookup_analysis("missing-id", FakeService)


def test_analyze_transcript_maps_configuration_errors_to_gradio_error() -> None:
    with pytest.raises(gr.Error, match="OPENAI_API_KEY is not configured."):
        analyze_transcript("Discuss roadmap.", MisconfiguredService)


def test_format_action_items_handles_empty_list() -> None:
    assert format_action_items(()) == "No suggested next steps returned."
