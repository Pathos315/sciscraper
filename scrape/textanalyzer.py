from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, order=True)
class AnalysisResult:
    """_summary_"""

    wordscore: int
    matching_terms: list[tuple[str, int]]
    mode_words: list[tuple[str, int]]
    research: list[tuple[str, int]]
    solution: list[tuple[str, int]]
    tech: list[tuple[str, int]]
    digital_object_id: str = "NaN"


class TextAnalyzer(Protocol):
    """TextAnalyzer _summary_

    Args:
        Protocol (_type_): _description_
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    def analyze(self, text_query: str) -> AnalysisResult:
        ...
