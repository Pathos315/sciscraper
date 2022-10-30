from enum import Enum
from time import perf_counter

from scrape.config import ScrapeConfig, read_config
from scrape.docscraper import DocScraper
from scrape.fetch import SciScraper
from scrape.jsonscraper import (DIMENSIONS_AI_KEYS, SEMANTIC_SCHOLAR_KEYS,
                                WebScraper)
from scrape.log import logger
from scrape.serials import SERIALIZERS
from scrape.utils import export_data

config = read_config("sciscraper/config.json")

SCRAPERS = {
    "PDF": DocScraper(config.bycatch_words,config.target_words),
    "SUMMARY": DocScraper(config.bycatch_words,config.target_words,is_pdf=False),
    "DIMENSIONS": WebScraper(config.citations_dataset_url, api_keys = DIMENSIONS_AI_KEYS)
}
def main() -> None:
    """Main function."""
    start = perf_counter()

    sci = SciScraper(config,serializer=SERIALIZERS["DIRECTORY"],scraper=SCRAPERS["PDF"],verbose_logging=True)
    #dimension = SciScraper(config,serializer=SERIALIZERS["DOI"],scraper=SCRAPERS["DIMENSIONS"],verbose_logging=True)
    #abstracts = SciScraper(config,serializer=SERIALIZERS["ABSTRACTS"],scraper=SCRAPERS["SUMMARY"],verbose_logging=True)
    scisc = sci.run(config.demo_dir)
    #dim = dimension.run(config.test_src)
    #summary = abstracts.run(dim)
    export_data(scisc)
    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
   