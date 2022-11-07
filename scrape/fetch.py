r"""Contains methods that take various files, which each
return varying dataframes or directories for each"""

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import pandas as pd
from tqdm import tqdm

from scrape.config import ScrapeConfig
from scrape.docscraper import DocScraper
from scrape.jsonscraper import WebScraper
from scrape.bulkpdf import BulkPDFScraper
from scrape.log import logger

SerializationStrategyFunction = Callable[[str|pd.DataFrame],Iterable[Any]]

@dataclass(slots=True)
class SciScraper:
    config: ScrapeConfig
    serializer: SerializationStrategyFunction
    scraper: DocScraper | WebScraper
    logger: logging.Logger = logger
    verbose_logging: bool = False

    def run(self, target: str|pd.DataFrame) -> pd.DataFrame:
        search_terms = self.serializer(target)
        data = (self.scraper.scrape(term) for term in tqdm(search_terms, desc="[sciscraper]: ", unit="papers"))
        data = (term for term in data if term != None)
        logger.debug(data)
        data = list(map(asdict,data))
        logger.debug(data)
        data = pd.DataFrame(data)
        title_terms = self.format_filename(search_terms)
        titles: pd.Series[str] = pd.Series(title_terms, name="titles")
        return data.join(titles)

    def format_filename(self, search_terms: Iterable[Any]):
        return [Path(term).name for term in search_terms]

    def toggle_logging_level(self):
        self.verbose_logging = not self.verbose_logging

@dataclass(slots=True)
class SciDownloader:
    config: ScrapeConfig
    serializer: SerializationStrategyFunction
    scraper: BulkPDFScraper
    logger: logging.Logger = logger
    verbose_logging: bool = False

    def run(self, target: str|pd.DataFrame) -> None:
        search_terms = self.serializer(target)
        for term in tqdm(search_terms, desc="[sciscraper]: ", unit="downloads"):
            self.scraper.download(term)

    def toggle_logging_level(self):
        self.verbose_logging = not self.verbose_logging