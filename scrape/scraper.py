from dataclasses import dataclass, field
from typing import Protocol


@dataclass(kw_only=True, slots=True, frozen=True, order=True)
class ScrapeResult:
    title: str
    publisher: str
    pub_date: str
    doi: str
    pub_id: str
    abstract: str
    journal_title: str
    volume: str
    issue: str
    times_cited: int
    author_list: list[str] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)
    cited_dimensions_ids: list[str] = field(default_factory=list)


@dataclass(kw_only=True, slots=True, frozen=True, order=True)
class WordscoreResult:
    wordscore: int
    most_freq_target_words: list = field(default_factory=list)
    most_freq_all_words: list = field(default_factory=list)
    study_design_hunch: list = field(default_factory=list)
    impact_of_study_hunch: list = field(default_factory=list)
    tech_words_freq: list = field(default_factory=list)


class Scraper(Protocol):
    def scrape(self, search_text: str) -> ScrapeResult | WordscoreResult:
        ...
