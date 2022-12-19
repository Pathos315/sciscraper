r"""Contains methods that take various files and directories, which each
returning various dataframes for each"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, is_dataclass
from typing import Generator, Optional, Callable, Iterable, Any

from random import randint
import pandas as pd
import numpy as np
from tqdm import tqdm
from sciscraper.scrape.config import FilePath, config
from sciscraper.scrape.docscraper import DocScraper, DocumentResult
from sciscraper.scrape.webscrapers import WebScraper, WebScrapeResult
from sciscraper.scrape.downloaders import Downloader, DownloadReceipt
from sciscraper.scrape.change_dir import change_dir
from sciscraper.scrape.log import logger

SerializationStrategyFunction = Callable[[FilePath], list[str]]
StagingStrategyFunction = Callable[[pd.DataFrame], Iterable[Any]]

KEY_TYPE_PAIRINGS: dict[str, Any] = {
    "title": "string",
    "doi": "string",
    "internal_id": "string",
    "times_cited": np.int16,
    "wordscore": np.float16,
    "abstract": "string",
    "biblio": "string",
    "journal_title": "string",
    "downloader": "string",
    "filepath": "string",
}


@dataclass(slots=True)
class Fetcher(ABC):
    """
    Fetcher is the overarching abstract class for fetching data
    from a given query.
    """

    scraper: DocScraper | WebScraper | Downloader

    @abstractmethod
    def __call__(self, *args, **kwargs) -> pd.DataFrame:
        """The __call__ method in ScrapeFetcher and StagingFetcher
        take a target FilePath or dataframe respectively.
        They are converted them into lists of entries.
        Next those lists are scraped in `fetch`, where they are
        passed into a Generator, which ultimately produces
        a list that's made into a pd.DataFrame.

        Returns
        -------
        pd.DataFrame
            A dataframe containing biliographic data.
        """

    def fetch(
        self, search_terms: list[str], tqdm_unit: str = "abstracts"
    ) -> pd.DataFrame:
        """
        fetch runs a scrape using the given
        search terms and
        returns a dataframe.

        Parameters
        ----------
        search_terms : list[str]
            A serialized list of terms to be scraped.

        Returns
        -------
        pd.DataFrame
            A dataframe containing biliographic data.
        """
        data: Generator[
            DocumentResult | WebScrapeResult | DownloadReceipt | None, None, None
        ] = (
            self.scraper.obtain(term)
            for term in tqdm(search_terms, desc="[sciscraper]: ", unit=f"{tqdm_unit}")
        )
        logger.debug(data)
        data = (item for item in data if is_dataclass(item) and item is not None)
        return pd.DataFrame(list(data), index=None)


@dataclass(slots=True)
class ScrapeFetcher(Fetcher):
    """
    ScrapeFetcher takes a string `target`
    serialized into a list of strings with serializer
    It then puts it into fetch, where it returns a dataframe.
    """

    serializer: SerializationStrategyFunction

    def __call__(self, target: FilePath) -> pd.DataFrame:
        search_terms: list[str] = self.serializer(target)
        return self.fetch(search_terms)


@dataclass(slots=True)
class StagingFetcher(Fetcher):
    """
    StagingFetcher takes a dataframe, `prior_df` with one of its columns
    isolated and staged, via `stager`, into a list of `staged_terms`.
    It then puts it into fetch, where it returns the final dataframe.
    """

    stager: StagingStrategyFunction

    def __call__(self, prior_df: pd.DataFrame) -> pd.DataFrame:
        staged_terms: Iterable[Any] = self.stager(prior_df)
        if isinstance(staged_terms, list):
            df_ext: pd.DataFrame = self.fetch(staged_terms)
            dataframe: pd.DataFrame = prior_df.join(df_ext)
        elif isinstance(staged_terms, tuple):
            citations, src_titles = staged_terms
            ref_df: pd.DataFrame = self.fetch(citations, "references")
            dataframe = ref_df.join(
                pd.Series(src_titles, dtype="string", name="src_titles")
            )
        else:
            raise ValueError("Staged terms must be lists or tuples.")
        return dataframe


@dataclass(slots=True)
class SciScraper:
    """
    Sciscraper is the base class for all
    operations within the sciscraper module.
    """

    scraper: ScrapeFetcher
    stager: Optional[StagingFetcher]
    logger = logger
    export_dir: str = config.export_dir

    def __call__(
        self, target: FilePath, export: bool = True, debug: bool = False
    ) -> None:
        self.logger.setLevel(10) if debug else self.logger.setLevel(20)
        logger.info(f"Debug logging status: '{debug}'\n")
        logger.info("Commencing scisciscraper.scrape...\n")
        df: pd.DataFrame = self.scraper(target)
        df = self.stager(df) if self.stager else df
        df = self.df_casting(df)
        if export:
            self.export(df)

    def df_casting(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Formats and optimizes the final dataframe through converting datatypes
        and filling missing fields, where possible.

        Returns
        -------
        pd.DataFrame
            A cleaned and optimized dataframe.
        """
        if not self.stager:
            return df

        # Convert "pub_date" column to datetime data type
        df["pub_date"] = pd.to_datetime(df["pub_date"], infer_datetime_format=True)

        # Convert columns in KEY_TYPE_PAIRINGS dictionary to specified data types
        for scikey, value in KEY_TYPE_PAIRINGS.items():
            if scikey in df:
                df[scikey] = df[scikey].astype(value)
        return df

    def export(self, dataframe: pd.DataFrame) -> None:
        """Export data to the specified export directory."""
        dataframe.info(verbose=True)
        logger.info(f"\n\n{dataframe.head(10)}")
        with change_dir(self.export_dir):
            print_id: int = randint(0, 100)
            export_name: str = f"{config.today}_sciscraper_{print_id}.csv"
            logger.info(
                f"A spreadsheet was exported as {export_name} in {self.export_dir}."
            )
            dataframe.to_csv(export_name)
