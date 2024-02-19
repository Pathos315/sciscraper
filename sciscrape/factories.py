"""`factories.py` is a module for constructing and executing scientific data scrapers.

This module contains functions and classes for scraping scientific data from various sources,
including the Dimensions.ai API and local directories.
It also includes functions for serializing and staging the scraped data.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path

from .config import config
from .docscraper import DocScraper
from .downloaders import BulkPDFScraper, ImagesDownloader
from .fetch import SciScraper, ScrapeFetcher, StagingFetcher
from .log import logger
from .serials import (
    serialize_from_csv,
    serialize_from_directory,
    serialize_from_txt,
)
from .stagers import stage_from_series, stage_with_reference
from .webscrapers import DimensionsScraper, GoogleScholarScraper

SCRAPERS: dict[str, ScrapeFetcher] = {
    "pdf_lookup": ScrapeFetcher(
        DocScraper(
            Path(config.target_words).resolve(),
            Path(config.bycatch_words).resolve(),
        ),
        serialize_from_directory,
    ),
    "csv_lookup": ScrapeFetcher(
        DimensionsScraper(config.dimensions_ai_dataset_url),
        serialize_from_csv,
    ),
    "abstract_lookup": ScrapeFetcher(
        DocScraper(
            Path(config.target_words).resolve(),
            Path(config.bycatch_words).resolve(),
            is_pdf=False,
        ),
        partial(
            serialize_from_csv,
            column="abstract",
        ),
        _title_serializer=partial(
            serialize_from_csv,
            column="title",
        ),
    ),
    "google_lookup": ScrapeFetcher(
        GoogleScholarScraper(config.google_scholar_url, config.sleep_interval, 2016, 2023, "j", 5),
        serialize_from_txt,
    ),
}


STAGERS: dict[str, StagingFetcher] = {
    "abstracts": StagingFetcher(
        DocScraper(
            Path(config.target_words).resolve(),
            Path(config.bycatch_words).resolve(),
            False,
        ),
        stage_from_series,
    ),
    "citations": StagingFetcher(
        DimensionsScraper(config.dimensions_ai_dataset_url),
        stage_with_reference,
    ),
    "download": StagingFetcher(BulkPDFScraper(config.downloader_url), partial(stage_from_series, column="doi")),
    "images": StagingFetcher(ImagesDownloader(url=""), partial(stage_with_reference, column_x="figures")),
    "pdf_expanded": StagingFetcher(
        DimensionsScraper(config.dimensions_ai_dataset_url), partial(stage_from_series, column="doi_from_pdf")
    ),
}


SCISCRAPERS: dict[str, SciScraper] = {
    "directory": SciScraper(SCRAPERS["pdf_lookup"], STAGERS["pdf_expanded"]),
    "wordscore": SciScraper(SCRAPERS["csv_lookup"], STAGERS["abstracts"]),
    "citations": SciScraper(SCRAPERS["csv_lookup"], STAGERS["citations"]),
    "download": SciScraper(SCRAPERS["csv_lookup"], STAGERS["download"]),
    "images": SciScraper(SCRAPERS["csv_lookup"], STAGERS["images"]),
    "fastscore": SciScraper(SCRAPERS["abstract_lookup"], None),
    "google": SciScraper(SCRAPERS["google_lookup"], None),
}


def read_factory() -> SciScraper:
    """
    Constructs an exporter factory based on the user's preference.

    Returns
    ------
    Sciscraper: An instance of Sciscraper, from which the program is run.
    """

    while True:
        scrape_process = input(f"Enter desired data scraping process ({', '.join(SCISCRAPERS)}): ")
        try:
            return SCISCRAPERS[scrape_process]
        except KeyError:
            logger.error("Unknown data scraping process option: %s.", scrape_process)
