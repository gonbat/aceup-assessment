class TranscriptAnalysisError(Exception):
    pass


class InvalidTranscriptError(TranscriptAnalysisError):
    pass


class AnalysisNotFoundError(TranscriptAnalysisError):
    pass


class LLMCompletionError(TranscriptAnalysisError):
    pass
