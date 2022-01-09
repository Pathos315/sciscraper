import time

from scrape.config import read_config
from scrape.export import export_data
from scrape.fetch import (
    fetch_citations_hence,
    fetch_terms_from_doi,
    fetch_terms_from_pdf_files,
)
from scrape.log import log_msg

__version__ = 2.0

source = #csv file path here

def main() -> None:

    # read the configuration settings from a JSON file
    config = read_config("./config.json")

    # fetch data from pdf files and export it
    start = time.perf_counter()
    initial = fetch_terms_from_doi(source)
    is_cited_in_result = fetch_citations_hence(initial)
    pdf_result = fetch_terms_from_pdf_files(config)
    
    #exports the data to csv files
    export_data(initial, config.export_dir)
    export_data(is_cited_in_result, config.export_dir)
    export_data(pdf_result, config.export_dir)
    
    elapsed = time.perf_counter() - start
    log_msg(f"\n[sciscraper]: Extraction finished in {elapsed} seconds.\n")


if __name__ == "__main__":
    main()
