r"""Contains methods that take various files and directories, which each
returning various dataframes for each"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, is_dataclass
from typing import (
    Iterator,
    Callable,
    Iterable,
    Any,
)

from random import randint
import pandas as pd
import numpy as np
from tqdm import tqdm
from sciscrape.config import FilePath, config
from sciscrape.docscraper import DocScraper, DocumentResult
from sciscrape.webscrapers import WebScraper, WebScrapeResult
from sciscrape.downloaders import Downloader, DownloadReceipt
from sciscrape.change_dir import change_dir
from sciscrape.log import logger

SerializationStrategyFunction = Callable[[FilePath], list[str]]
StagingStrategyFunction = Callable[[pd.DataFrame], Iterable[Any]]
ScrapeResult = DocumentResult | WebScrapeResult | DownloadReceipt


KEY_TYPE_PAIRINGS: dict[str, Any] = {
    "title": "string",
    "doi": "string",
    "internal_id": "string",
    "times_cited": np.int16,
    "matching_terms": np.int16,
    "bycatch_terms": np.int16,
    "total_length": np.int16,
    "wordscore": np.float16,
    "expectation": np.float16,
    "variance": np.float16,
    "standard_deviation": np.float16,
    "skewness": np.float16,
    "abstract": "string",
    "biblio": "string",
    "journal_title": "string",
    "downloader": "string",
    "filepath": "string",
}


@dataclass
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
        data: Iterator[ScrapeResult | None] = (
            self.scraper.obtain(term)
            for term in tqdm(search_terms, desc="[sciscraper]: ", unit=f"{tqdm_unit}")
        )
        logger.debug(data)
        data = (item for item in data if is_dataclass(item) and item is not None)
        return pd.DataFrame(list(data), index=None)


@dataclass
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


@dataclass
class StagingFetcher(Fetcher):
    """
    StagingFetcher takes a dataframe, `prior_dataframe` with one of its columns
    isolated and staged, via `stager`, into a list of `staged_terms`.
    It then puts it into fetch, where it returns the final dataframe.
    """

    stager: StagingStrategyFunction

    def __call__(self, prior_dataframe: pd.DataFrame) -> pd.DataFrame:
        staged_terms: Iterable[Any] = self.stager(prior_dataframe)
        if isinstance(staged_terms, list):
            dataframe = self.fetch_from_staged_series(prior_dataframe, staged_terms)
        elif isinstance(staged_terms, tuple):
            dataframe = self.fetch_with_staged_reference(staged_terms)  # type: ignore
        else:
            raise ValueError("Staged terms must be lists or tuples.")
        return dataframe

    def fetch_from_staged_series(
        self, prior_dataframe: pd.DataFrame, staged_terms: list
    ) -> pd.DataFrame:
        """If the terms are staged as a list, then the dataframe is extended
        along the provided query, and then it is appended to the existing dataframe."""
        dataframe_ext: pd.DataFrame = self.fetch(staged_terms)
        dataframe: pd.DataFrame = prior_dataframe.join(dataframe_ext)
        return dataframe

    def fetch_with_staged_reference(
        self,
        staged_terms: tuple[
            list[Any],
            list[Any],
        ],
    ) -> pd.DataFrame:
        """If the terms are staged as a tuple of two lists,
        then the first part of the tuple gets extended
        along the provided query. Then the second part of the tuple gets
        exploded out and appended. The default version of this
        provide the source titles, from which the ensuing citations
        were originally found. The prior dataframe is not kept."""
        citations, src_titles = staged_terms
        ref_dataframe = self.fetch(citations, "references")
        dataframe = ref_dataframe.join(
            pd.Series(
                src_titles,
                dtype="string",
                name="src_titles",
            )
        )
        return dataframe


@dataclass
class SciScraper:
    """
    Sciscraper is the base class for all
    operations within the sciscraper module.
    """

    scraper: ScrapeFetcher
    stager: StagingFetcher | None
    logger = logger
    downcast: bool = True

    def __call__(
        self, target: FilePath, export: bool = True, debug: bool = False
    ) -> None:
        self.set_logging(debug)
        logger.info(
            "Debug logging status: '%s'\n"
            "Commencing sciscrape on file: '%s'...\n",
            debug,
            target
        )
        dataframe: pd.DataFrame = self.scraper(target)
        dataframe = self.stager(dataframe) if self.stager else dataframe
        dataframe = self.remove_empty_columns(dataframe)
        dataframe = self.dataframe_casting(dataframe) if self.downcast else dataframe
        self.export(dataframe) if export else None

    def set_logging(self, debug: bool) -> None:
        """Sets the logging level to debug if specified,
        otherwise, it defaults to info logging."""
        self.logger.setLevel(10) if debug else self.logger.setLevel(20)

    def remove_empty_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Removes all empty columns in the dataframe before exporting to .csv."""
        return dataframe.replace("", float("NaN")).dropna(how="all", axis=1)

    @staticmethod
    def dataframe_casting(dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Formats and optimizes the final dataframe through converting datatypes
        and filling missing fields, where possible.

        Returns
        -------
        pd.DataFrame
            A cleaned and optimized dataframe.
        """

        # Convert "pub_date" column to datetime data type
        if "pub_date" in dataframe:
            dataframe["pub_date"] = SciScraper.downcast_available_datetimes(dataframe)

        # Convert columns in KEY_TYPE_PAIRINGS dictionary to specified data types
        for scikey, value in KEY_TYPE_PAIRINGS.items():
            if scikey in dataframe:
                dataframe[scikey] = dataframe[scikey].astype(value)
        return dataframe

    @staticmethod
    def downcast_available_datetimes(dataframe: pd.DataFrame | pd.Series):
        """Converts all paper publication dates to the datetime format."""
        return pd.to_datetime(dataframe["pub_date"], infer_datetime_format=True)

    @staticmethod
    def export(
        dataframe: pd.DataFrame, export_dir: str = config.export_dir
    ) -> None:
        """Export data to the specified export directory."""
        SciScraper.dataframe_logging(dataframe)
        export_name = SciScraper.create_export_name()
        with change_dir(export_dir):
            logger.info(
                "A spreadsheet was exported as %s in %s.",
                export_name,
                export_dir
            )
            dataframe.to_csv(export_name, index=False)

    @staticmethod
    def dataframe_logging(dataframe: pd.DataFrame) -> None:
        """Returns the first ten rows of the dataframe into the logger."""
        dataframe.info(verbose=True)
        logger.info("\n\n%s", dataframe.head(10))

    @staticmethod
    def create_export_name() -> str:
        """Returns a `export_name` for the spreadsheet with
        both today's date and a randomly generated `print_id`
        number."""
        print_id = randint(0, 100)
        export_name = f"{config.today}_sciscraper_{print_id}.csv"
        return export_name
