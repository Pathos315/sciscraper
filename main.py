import time

from scrape.config import read_config
from scrape.fetch import (
    fetch_abstracts_from_csv,
    fetch_abstracts_from_dataframe,
    fetch_citations_hence,
    fetch_terms_from_doi,
    fetch_terms_from_pdf_files,
    fetch_terms_from_titles,
)
from scrape.utils import export_data


def main() -> None:
    """main _summary_"""
    # read the configuration settings from a JSON file
    config = read_config("./config.json")

    # fetch data from pdf files and export it
    start = time.perf_counter()
    # first = fetch_terms_from_doi(config.prime_src, config)
    # export_data(first, config.export_dir)
    first = fetch_terms_from_titles(config.prime_src, config)
    # second = fetch_abstracts_from_dataframe(target=first, config=config)
    # result = fetch_citations_hence(initial, config)
    # result = fetch_terms_from_pdf_files(config)
    export_data(first, config.export_dir)
    elapsed = time.perf_counter() - start
    print(f"\n[sciscraper]: Extraction finished in {elapsed} seconds.\n")


if __name__ == "__main__":
    main()
