class TranscriptAnalysisError(Exception):
    pass


class InvalidTranscriptError(TranscriptAnalysisError):
    pass


class AnalysisNotFoundError(TranscriptAnalysisError):
    pass


class ConfigurationError(TranscriptAnalysisError):
    pass


class LLMCompletionError(TranscriptAnalysisError):
    pass
