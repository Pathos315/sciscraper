from time import perf_counter

from scrape.config import read_config
from scrape.fetch import (fetch_abstracts_from_csv,
                          fetch_abstracts_from_dataframe,
                          fetch_citations_hence, fetch_terms_from_csv,
                          fetch_terms_from_pdf_files)
from scrape.log import logger
from scrape.utils import export_data


def main() -> None:
    """main _summary_"""
    # read the configuration settings from a JSON file

    config = read_config("./config.json")

    # fetch data from pdf files and export it
    start = perf_counter()
    doi_results = fetch_terms_from_csv(config.prime_src, "doi", config)
    abstract_results = fetch_abstracts_from_dataframe(target=doi_results, config=config)
    # result = fetch_citations_hence(initial, config)
    # result = fetch_terms_from_pdf_files(config)
    export_data(abstract_results, config.export_dir)
    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed} seconds.")


if __name__ == "__main__":
    main()
