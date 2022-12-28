from functools import partial
from sciscrape.docscraper import DocScraper
from sciscrape.webscrapers import DimensionsScraper
from sciscrape.downloaders import BulkPDFScraper, ImagesDownloader
from sciscrape.stagers import stage_from_series, stage_with_reference
from sciscrape.serials import serialize_from_csv, serialize_from_directory
from sciscrape.fetch import SciScraper, ScrapeFetcher, StagingFetcher
from sciscrape.config import config
from sciscrape.log import logger

# SCRAPERS
pdf_lookup = ScrapeFetcher(
    DocScraper(config.target_words, config.bycatch_words), serialize_from_directory
)
csv_lookup = ScrapeFetcher(
    DimensionsScraper(config.dimensions_ai_dataset_url), serialize_from_csv
)
abstract_lookup = ScrapeFetcher(
    DocScraper(config.target_words, config.bycatch_words, False),
    partial(serialize_from_csv, column="abstract"),
)

# STAGERS
abstracts = StagingFetcher(
    DocScraper(config.target_words, config.bycatch_words, False), stage_from_series
)
citations = StagingFetcher(
    DimensionsScraper(config.dimensions_ai_dataset_url), stage_with_reference
)
references = StagingFetcher(
    DimensionsScraper(config.dimensions_ai_dataset_url, query_subset_citations=True),
    stage_with_reference,
)
download = StagingFetcher(
    BulkPDFScraper(config.downloader_url), partial(stage_from_series, column="doi")
)
images = StagingFetcher(
    ImagesDownloader(url=""), partial(stage_with_reference, column_x="figures")
)


SCISCRAPERS: dict[str, SciScraper] = {
    "directory": SciScraper(pdf_lookup, None),
    "wordscore": SciScraper(csv_lookup, abstracts),
    "citations": SciScraper(csv_lookup, citations),
    "reference": SciScraper(csv_lookup, references),
    "download": SciScraper(csv_lookup, download),
    "images": SciScraper(csv_lookup, images),
    "vfscore": SciScraper(abstract_lookup, None),
}


def read_factory() -> SciScraper:
    """
    Constructs an exporter factory based on the user's preference.
    """

    while True:
        scrape_process: str = input(
            f"Enter desired data scraping process ({', '.join(SCISCRAPERS)}): "
        )
        try:
            return SCISCRAPERS[scrape_process]
        except KeyError:
            logger.error(f"Unknown data scraping process option: {scrape_process}.")
