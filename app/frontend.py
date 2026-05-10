from collections.abc import Callable
from html import escape

import gradio as gr

from app.domain import TranscriptAnalysis
from app.errors import (
    AnalysisNotFoundError,
    ConfigurationError,
    InvalidTranscriptError,
    LLMCompletionError,
)
from app.services import TranscriptAnalysisService

ServiceFactory = Callable[[], TranscriptAnalysisService]
FrontendResult = tuple[str, str, str]
LoadingFrontendResult = tuple[dict[str, object], dict[str, object], str, dict[str, object]]
AnalysisFrontendResult = tuple[dict[str, object], str]
CleanupFrontendResult = tuple[dict[str, object], dict[str, object]]
FailureFrontendResult = tuple[dict[str, object], dict[str, object], str, dict[str, object]]

APP_CSS = """
.analysis-status {
    margin-top: 0.75rem;
    width: 100%;
}

.analysis-status__content {
    align-items: center;
    background: var(--background-fill-secondary);
    border: 1px solid var(--border-color-primary);
    border-radius: 8px;
    color: var(--body-text-color);
    display: flex;
    font-size: 0.95rem;
    gap: 0.65rem;
    line-height: 1.35;
    min-height: 2.75rem;
    padding: 0.7rem 0.9rem;
    white-space: normal;
    width: 100%;
}

.analysis-status__spinner {
    animation: analysis-spin 0.8s linear infinite;
    border: 2px solid var(--border-color-primary);
    border-top-color: var(--button-primary-background-fill);
    border-radius: 999px;
    flex: 0 0 auto;
    height: 1rem;
    width: 1rem;
}

.analysis-status--error .analysis-status__content {
    border-color: var(--error-border-color, #d33);
    color: var(--error-text-color, #b00020);
}

@keyframes analysis-spin {
    to {
        transform: rotate(360deg);
    }
}

.analysis-result {
    background: var(--background-fill-primary);
    border: 1px solid var(--border-color-primary);
    border-radius: 8px;
    margin-top: 1rem;
    padding: 1rem 1.125rem;
}

.analysis-result h3 {
    font-size: 1rem;
    font-weight: 650;
    margin: 1rem 0 0.35rem;
}

.analysis-result h3:first-child {
    margin-top: 0;
}

.analysis-result p,
.analysis-result ol {
    margin-top: 0;
}
"""


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

            analysis_status_output = gr.HTML(
                visible=False,
                elem_classes=["analysis-status"],
            )
            with gr.Group(visible=False, elem_classes=["analysis-result"]) as analysis_result_group:
                analysis_result_output = gr.Markdown(
                    container=False,
                    line_breaks=True,
                    buttons=["copy"],
                )

            analyze_event = analyze_button.click(
                fn=show_analyze_loading,
                outputs=[
                    analysis_status_output,
                    analysis_result_group,
                    analysis_result_output,
                    analyze_button,
                ],
            ).then(
                fn=lambda transcript: analyze_transcript_for_ui(transcript, service_factory),
                inputs=transcript_input,
                outputs=[
                    analysis_result_group,
                    analysis_result_output,
                ],
            )
            analyze_event.success(
                fn=hide_analyze_loading,
                outputs=[analysis_status_output, analyze_button],
            )
            analyze_event.failure(
                fn=show_analyze_failure,
                outputs=[
                    analysis_status_output,
                    analysis_result_group,
                    analysis_result_output,
                    analyze_button,
                ],
            )

        with gr.Tab("Lookup"):
            analysis_id_input = gr.Textbox(label="Analysis ID")
            lookup_button = gr.Button("Lookup", variant="primary")

            lookup_status_output = gr.HTML(
                visible=False,
                elem_classes=["analysis-status"],
            )
            with gr.Group(visible=False, elem_classes=["analysis-result"]) as lookup_result_group:
                lookup_result_output = gr.Markdown(
                    container=False,
                    line_breaks=True,
                    buttons=["copy"],
                )

            lookup_event = lookup_button.click(
                fn=show_lookup_loading,
                outputs=[
                    lookup_status_output,
                    lookup_result_group,
                    lookup_result_output,
                    lookup_button,
                ],
            ).then(
                fn=lambda analysis_id: lookup_analysis_for_ui(analysis_id, service_factory),
                inputs=analysis_id_input,
                outputs=[
                    lookup_result_group,
                    lookup_result_output,
                ],
            )
            lookup_event.success(
                fn=hide_lookup_loading,
                outputs=[lookup_status_output, lookup_button],
            )
            lookup_event.failure(
                fn=show_lookup_failure,
                outputs=[
                    lookup_status_output,
                    lookup_result_group,
                    lookup_result_output,
                    lookup_button,
                ],
            )

    return frontend


def show_analyze_loading() -> LoadingFrontendResult:
    return show_loading("Analyzing transcript...", "Analyzing...")


def show_lookup_loading() -> LoadingFrontendResult:
    return show_loading("Looking up analysis...", "Looking up...")


def show_loading(message: str, button_label: str) -> LoadingFrontendResult:
    return (
        gr.update(value=format_status_html(message), visible=True),
        gr.update(visible=False),
        "",
        gr.update(value=button_label, interactive=False),
    )


def hide_analyze_loading() -> CleanupFrontendResult:
    return hide_loading("Analyze")


def hide_lookup_loading() -> CleanupFrontendResult:
    return hide_loading("Lookup")


def hide_loading(button_label: str) -> CleanupFrontendResult:
    return gr.update(value="", visible=False), gr.update(value=button_label, interactive=True)


def show_analyze_failure() -> FailureFrontendResult:
    return show_failure("Analyze")


def show_lookup_failure() -> FailureFrontendResult:
    return show_failure("Lookup")


def show_failure(button_label: str) -> FailureFrontendResult:
    return (
        gr.update(
            value=format_status_html("Could not complete the request.", is_error=True),
            visible=True,
        ),
        gr.update(visible=False),
        "",
        gr.update(value=button_label, interactive=True),
    )


def analyze_transcript_for_ui(
    transcript: str,
    service_factory: ServiceFactory,
) -> AnalysisFrontendResult:
    return show_result(*analyze_transcript(transcript, service_factory))


def analyze_transcript(transcript: str, service_factory: ServiceFactory) -> FrontendResult:
    try:
        analysis = service_factory().analyze(transcript)
    except (ConfigurationError, InvalidTranscriptError, LLMCompletionError) as exc:
        raise gr.Error(str(exc)) from exc

    return format_analysis(analysis)


def lookup_analysis_for_ui(
    analysis_id: str,
    service_factory: ServiceFactory,
) -> AnalysisFrontendResult:
    return show_result(*lookup_analysis(analysis_id, service_factory))


def lookup_analysis(analysis_id: str, service_factory: ServiceFactory) -> FrontendResult:
    try:
        analysis = service_factory().get(analysis_id.strip())
    except (AnalysisNotFoundError, ConfigurationError, InvalidTranscriptError, LLMCompletionError) as exc:
        raise gr.Error(str(exc)) from exc

    return format_analysis(analysis)


def show_result(
    analysis_id: str,
    summary: str,
    action_items: str,
) -> AnalysisFrontendResult:
    return (
        gr.update(visible=True),
        format_result_markdown(analysis_id, summary, action_items),
    )


def format_analysis(analysis: TranscriptAnalysis) -> FrontendResult:
    return analysis.id, analysis.summary, format_action_items(analysis.action_items)


def format_status_html(message: str, is_error: bool = False) -> str:
    status_class = "analysis-status--error" if is_error else ""
    spinner = "" if is_error else '<span class="analysis-status__spinner" aria-hidden="true"></span>'
    role = "alert" if is_error else "status"

    return (
        f'<div class="{status_class}">'
        f'<div class="analysis-status__content" role="{role}">'
        f"{spinner}<span>{escape(message)}</span>"
        "</div>"
        "</div>"
    )


def format_result_markdown(analysis_id: str, summary: str, action_items: str) -> str:
    return f"""### Analysis ID
`{analysis_id}`

### Summary
{summary}

### Suggested Next Steps
{action_items}
"""


def format_action_items(action_items: tuple[str, ...]) -> str:
    if not action_items:
        return "No suggested next steps returned."

    return "\n".join(
        f"{index}. {action_item}" for index, action_item in enumerate(action_items, start=1)
    )
