"""`factories.py` is a module for constructing and executing scientific data scrapers.

This module contains functions and classes for scraping scientific data from various sources,
including the Dimensions.ai API and local directories.
It also includes functions for serializing and staging the scraped data.
"""

from functools import partial
from sciscrape.docscraper import DocScraper
from sciscrape.webscrapers import DimensionsScraper
from sciscrape.downloaders import BulkPDFScraper, ImagesDownloader
from sciscrape.stagers import stage_from_series, stage_with_reference
from sciscrape.serials import serialize_from_csv, serialize_from_directory
from sciscrape.fetch import SciScraper, ScrapeFetcher, StagingFetcher
from sciscrape.config import config
from sciscrape.log import logger

SCRAPERS: dict[str, ScrapeFetcher] = {
    "pdf_lookup": ScrapeFetcher(
        DocScraper(
            config.target_words,
            config.bycatch_words,
        ),
        serialize_from_directory,
    ),
    "csv_lookup": ScrapeFetcher(
        DimensionsScraper(config.dimensions_ai_dataset_url),
        serialize_from_csv,
    ),
    "abstract_lookup": ScrapeFetcher(
        DocScraper(
            config.target_words,
            config.bycatch_words,
            is_pdf=False,
        ),
        partial(
            serialize_from_csv,
            column="abstract",
        ),
    ),
}

STAGERS: dict[str, StagingFetcher] = {
    "abstracts": StagingFetcher(
        DocScraper(
            config.target_words,
            config.bycatch_words,
            False,
        ),
        stage_from_series,
    ),
    "citations": StagingFetcher(
        DimensionsScraper(config.dimensions_ai_dataset_url),
        stage_with_reference,
    ),
    "references": StagingFetcher(
        DimensionsScraper(
            config.dimensions_ai_dataset_url,
            query_subset_citations=True,
        ),
        stage_with_reference,
    ),
    "download": StagingFetcher(
        BulkPDFScraper(config.downloader_url), partial(stage_from_series, column="doi")
    ),
    "images": StagingFetcher(
        ImagesDownloader(url=""), partial(stage_with_reference, column_x="figures")
    ),
}


SCISCRAPERS: dict[str, SciScraper] = {
    "directory": SciScraper(SCRAPERS["pdf_lookup"], None),
    "wordscore": SciScraper(SCRAPERS["csv_lookup"], STAGERS["abstracts"]),
    "citations": SciScraper(SCRAPERS["csv_lookup"], STAGERS["citations"]),
    "reference": SciScraper(SCRAPERS["csv_lookup"], STAGERS["references"]),
    "download": SciScraper(SCRAPERS["csv_lookup"], STAGERS["download"]),
    "images": SciScraper(SCRAPERS["csv_lookup"], STAGERS["images"]),
    "_vfscore": SciScraper(SCRAPERS["abstract_lookup"], None),
}


def read_factory() -> SciScraper:
    """
    Constructs an exporter factory based on the user's preference.

    Returns
    ------
    Sciscraper: An instance of Sciscraper, from which the program is run.
    """

    while True:
        scrape_process: str = input(
            f"Enter desired data scraping process ({', '.join(SCISCRAPERS)}): "
        )
        try:
            return SCISCRAPERS[scrape_process]
        except KeyError:
            logger.error("Unknown data scraping process option: %s.", scrape_process)
