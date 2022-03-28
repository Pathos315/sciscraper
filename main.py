from time import perf_counter

from scrape.config import read_config
from scrape.fetch import SciScraper, filter_neg_wordscores
from scrape.log import logger
from scrape.utils import export_data

config = read_config("./config.json")

doi = SciScraper(config.prime_src, config, scrape_key="doi", column="doi")
pub = SciScraper(config.prime_src, config, scrape_key="pub", column="id")
pdf = SciScraper(config.research_dir, config, scrape_key="pdf")
abstracts = SciScraper(config.prime_src, "abstract", config, scrape_key="abstract")
hence = SciScraper(config.prime_src, "abstract", config, scrape_key="hence")


def main() -> None:
    """main _summary_"""
    # read the configuration settings from a JSON file

    # fetch data from pdf files and export it
    start = perf_counter()
    doi_results = doi.sciscrape()
    export_data(doi_results, config.export_dir)
    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed} seconds.")


if __name__ == "__main__":
    main()
