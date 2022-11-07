from functools import partial
from scrape.serials import serialize_from_series, serialize_from_directory, serialize_from_csv
from scrape.docscraper import DocScraper
from scrape.jsonscraper import WebScraper, DIMENSIONS_AI_KEYS, SEMANTIC_SCHOLAR_KEYS
from scrape.fetch import SciScraper, SciDownloader
from scrape.config import read_config
from scrape.bulkpdf import BulkPDFScraper
from scrape.log import logger

config = read_config("./sciscraper/config.json")

SERIALIZERS = {
    "directory":serialize_from_directory,
    "abstracts": serialize_from_series,
    "doi_csv": serialize_from_csv,
    "names": partial(serialize_from_csv, column="Name"),
    "doi_series": partial(serialize_from_series, column="doi")
}

SCRAPERS = {
    "pdf": DocScraper(config.bycatch_words,config.target_words),
    "summary": DocScraper(config.bycatch_words,config.target_words,is_pdf=False),
    "dimensions": WebScraper(config.citations_dataset_url, api_keys = DIMENSIONS_AI_KEYS),
    "semantic": WebScraper(config.citations_dataset_url, api_keys = SEMANTIC_SCHOLAR_KEYS),
    "scihub": BulkPDFScraper(config.export_dir, config.downloader_url)
}

SCISCRAPERS = {
    "pdfs": SciScraper(config,serializer=SERIALIZERS["directory"],scraper=SCRAPERS["pdf"]),
    "dimensions": SciScraper(config,serializer=SERIALIZERS["doi_csv"],scraper=SCRAPERS["dimensions"]),
    "semantic": SciScraper(config,serializer=SERIALIZERS["doi_csv"],scraper=SCRAPERS["semantic"]),
    "summarize": SciScraper(config,serializer=SERIALIZERS["abstracts"],scraper=SCRAPERS["summary"]),
}

SCIDOWNLOADER = {
    "scihub": SciDownloader(config,serializer=SERIALIZERS["doi_csv"],scraper=SCRAPERS["scihub"]),
}

def read_factory(debug: bool = False) -> SciScraper:
    """Constructs an exporter factory based on the user's preference."""

    while True:
        scrape_process = input(
            f"Enter desired data scraping process ({', '.join(SCISCRAPERS)}): "
        )
        try:
            if debug:
                SCISCRAPERS[scrape_process].toggle_logging_level()
                logger.info(f"Debug logging active: '{SCISCRAPERS[scrape_process].verbose_logging}")
                return SCISCRAPERS[scrape_process]
            else:
                logger.info(f"Debug logging active: '{SCISCRAPERS[scrape_process].verbose_logging}")
                return SCISCRAPERS[scrape_process]
        except KeyError:
            logger.error(f"Unknown data scraping process option: {scrape_process}.")

def read_downloader(debug: bool = False) -> SciDownloader:
    """Constructs an exporter factory based on the user's preference."""

    while True:
        scrape_process = input(
            f"Enter desired data scraping process ({', '.join(SCIDOWNLOADER)}): "
        )
        try:
            if debug:
                SCIDOWNLOADER[scrape_process].toggle_logging_level()
                logger.info(f"Debug logging active: '{SCIDOWNLOADER[scrape_process].verbose_logging}")
                return SCIDOWNLOADER[scrape_process]
            else:
                logger.info(f"Debug logging active: '{SCISCRAPERS[scrape_process].verbose_logging}")
                return SCIDOWNLOADER[scrape_process]
        except KeyError:
            logger.error(f"Unknown data scraping process option: {scrape_process}.")