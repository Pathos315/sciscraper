from time import perf_counter

from scrape.config import read_config
from scrape.fetch import SciScraper
from scrape.log import logger
from scrape.utils import export_data

this_config = read_config("./config.json")


def read_scraper():
    factories = {
        "csv": SciScraper(
            target=this_config.prime_src,
            config=this_config,
            scrape_key="doi",
            column="doi",  # type: ignore
        ),
        "id": SciScraper(
            target=this_config.prime_src,
            config=this_config,
            scrape_key="pub",
            column="id",  # type: ignore
        ),
        "pdf": SciScraper(
            target=this_config.research_dir, config=this_config, scrape_key="pdf"
        ),
        "abstracts": SciScraper(
            target=this_config.prime_src,
            config=this_config,
            scrape_key="abstract",
            column="abstract",  # type: ignore
        ),
        "deriv": SciScraper(
            target=this_config.prime_src,
            column="abstract",  # type: ignore
            config=this_config,
            scrape_key="deriv",
        ),
    }
    while True:
        chosen_process = input(
            "Enter desired process (csv, id, pdf, abstracts, derived): "
        )
        if chosen_process in factories:
            return factories[chosen_process]
        logger.error("Unknown value detected: %s" % chosen_process)


def main() -> None:
    """Main function."""
    start = perf_counter()
    fac = read_scraper()
    doi_results = fac.sciscrape()
    export_data(doi_results, this_config.export_dir)
    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed} seconds.")


if __name__ == "__main__":
    main()
