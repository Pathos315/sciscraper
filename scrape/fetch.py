r"""Contains methods that take various files, which each
return varying dataframes or directories for each"""

import logging
from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable

import pandas as pd
from tqdm import tqdm

from scrape.config import ScrapeConfig
from scrape.docscraper import DocScraper
from scrape.jsonscraper import WebScraper
from scrape.utils import logger

SerializationStrategyFunction = Callable[[str|pd.DataFrame],Iterable[Any]]

@dataclass
class SciScraper:
    config: ScrapeConfig
    serializer: SerializationStrategyFunction
    scraper: DocScraper | WebScraper
    logger: logging.Logger = logger
    verbose_logging: bool = False

    def run(self, target: str|pd.DataFrame) -> pd.DataFrame:
        search_terms = self.serializer(target)
        data = (self.scraper.scrape(term) for term in tqdm(search_terms))
        data = (term for term in data if term != None)
        logger.debug(data)
        data = list(map(asdict,data))
        logger.debug(data)
        dataframe = pd.DataFrame(data)
        return dataframe

    def logging_level(self):
        return logger.setLevel(10) if self.verbose_logging else logger.setLevel(20)
