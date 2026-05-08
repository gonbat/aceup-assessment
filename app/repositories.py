from typing import Protocol
from threading import RLock

from app.domain import TranscriptAnalysis


class TranscriptAnalysisRepository(Protocol):
    def save(self, analysis: TranscriptAnalysis) -> None:
        pass

    def get(self, analysis_id: str) -> TranscriptAnalysis | None:
        pass


class InMemoryTranscriptAnalysisRepository:
    def __init__(self) -> None:
        self._analyses: dict[str, TranscriptAnalysis] = {}
        self._lock = RLock()

    def save(self, analysis: TranscriptAnalysis) -> None:
        with self._lock:
            self._analyses[analysis.id] = analysis

    def get(self, analysis_id: str) -> TranscriptAnalysis | None:
        with self._lock:
            return self._analyses.get(analysis_id)
