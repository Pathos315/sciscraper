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

config = read_config("./config.json")

class Scrapers(Enum):
    PDF = DocScraper(config.bycatch_words,config.target_words)
    SUMMARY = DocScraper(config.bycatch_words,config.target_words,is_pdf=False)
    DIMENSIONS = WebScraper(config.citations_dataset_url, api_keys = DIMENSIONS_AI_KEYS)
    SEMANTIC_SCHOLAR = WebScraper(config.citations_dataset_url, api_keys = SEMANTIC_SCHOLAR_KEYS)

class SciScraper_Prefabs(Enum):
    SCRAPE_DIRECTORY = SciScraper(config,serializer=SERIALIZERS["DIRECTORY"],scraper=Scrapers.PDF.value)
    SCRAPE_DIMENSIONS_AI = SciScraper(config,serializer=SERIALIZERS["DOI"],scraper=Scrapers.DIMENSIONS.value)
    GET_ABSTACTS_FROM_DATAFRAME = SciScraper(config,serializer=SERIALIZERS["ABSTRACTS"],scraper=Scrapers.SUMMARY.value)

#Common Scrapers
scicraper = SciScraper_Prefabs.SCRAPE_DIRECTORY.value
dimension = SciScraper_Prefabs.SCRAPE_DIMENSIONS_AI.value
abstracts = SciScraper_Prefabs.GET_ABSTACTS_FROM_DATAFRAME.value

# dim = dimension.run(config.test_src)
# summary = abstracts.run(dim)
# e.g. get_summary_from_dimensions_ai = get_abstracts_from_dataframe.run(scrape_dimensions_ai)

def main() -> None:
    """Main function."""
    start = perf_counter()
    scidf = scicraper.run(config.demo_dir)

    export_data(scidf)
    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
   