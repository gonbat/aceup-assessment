from collections.abc import Callable

import gradio as gr

from app.domain import TranscriptAnalysis
from app.errors import AnalysisNotFoundError, InvalidTranscriptError, LLMCompletionError
from app.services import TranscriptAnalysisService

ServiceFactory = Callable[[], TranscriptAnalysisService]
FrontendResult = tuple[str, str, str]


def build_gradio_app(service_factory: ServiceFactory) -> gr.Blocks:
    with gr.Blocks(title="Transcript Analysis") as frontend:
        gr.Markdown("# Transcript Analysis")

        with gr.Tab("Analyze"):
            transcript_input = gr.Textbox(
                label="Transcript",
                lines=12,
                placeholder="Paste a transcript here...",
            )
            analyze_button = gr.Button("Analyze", variant="primary")

            analysis_id_output = gr.Textbox(label="Analysis ID", interactive=False)
            summary_output = gr.Textbox(label="Summary", lines=5, interactive=False)
            action_items_output = gr.Textbox(
                label="Suggested Next Steps",
                lines=6,
                interactive=False,
            )

            analyze_button.click(
                fn=lambda transcript: analyze_transcript(transcript, service_factory),
                inputs=transcript_input,
                outputs=[analysis_id_output, summary_output, action_items_output],
            )

        with gr.Tab("Lookup"):
            analysis_id_input = gr.Textbox(label="Analysis ID")
            lookup_button = gr.Button("Lookup", variant="primary")

            lookup_id_output = gr.Textbox(label="Analysis ID", interactive=False)
            lookup_summary_output = gr.Textbox(label="Summary", lines=5, interactive=False)
            lookup_action_items_output = gr.Textbox(
                label="Suggested Next Steps",
                lines=6,
                interactive=False,
            )

            lookup_button.click(
                fn=lambda analysis_id: lookup_analysis(analysis_id, service_factory),
                inputs=analysis_id_input,
                outputs=[lookup_id_output, lookup_summary_output, lookup_action_items_output],
            )

    return frontend


def analyze_transcript(transcript: str, service_factory: ServiceFactory) -> FrontendResult:
    try:
        analysis = service_factory().analyze(transcript)
    except (InvalidTranscriptError, LLMCompletionError) as exc:
        raise gr.Error(str(exc)) from exc

    return format_analysis(analysis)


def lookup_analysis(analysis_id: str, service_factory: ServiceFactory) -> FrontendResult:
    try:
        analysis = service_factory().get(analysis_id.strip())
    except (AnalysisNotFoundError, InvalidTranscriptError, LLMCompletionError) as exc:
        raise gr.Error(str(exc)) from exc

    return format_analysis(analysis)


def format_analysis(analysis: TranscriptAnalysis) -> FrontendResult:
    return analysis.id, analysis.summary, format_action_items(analysis.action_items)


def format_action_items(action_items: tuple[str, ...]) -> str:
    if not action_items:
        return "No suggested next steps returned."

    return "\n".join(f"{index}. {action_item}" for index, action_item in enumerate(action_items, start=1))
