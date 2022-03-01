from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, order=True)
class AnalysisResult:

    wordscore: int
    matching_terms: list[tuple[str, int]]
    mode_words: list[tuple[str, int]]
    research: list[tuple[str, int]]
    solution: list[tuple[str, int]]
    tech: list[tuple[str, int]]


class TextAnalyzer(Protocol):
    def analyze(self, text_query: str) -> AnalysisResult:
        ...
