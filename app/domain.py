from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptAnalysis:
    id: str
    summary: str
    action_items: tuple[str, ...]
