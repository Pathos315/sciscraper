import time

from scrape.config import read_config
from scrape.export import export_data
from scrape.fetch import (
    fetch_citations_hence,
    fetch_terms_from_doi,
    fetch_terms_from_pdf_files,
)
from scrape.log import log_msg

# source /Users/johnfallot/all_venvs/sciscraper2_venv/bin/activate
# this_venv = subprocess.run('source /Users/johnfallot/all_venvs/sciscraper2_venv/bin/activate')

source = "/Users/johnfallot/Downloads/Ideas and Evidence 31429ac75bc546a8b7ebe537ce9cea89 2.csv"


def main() -> None:

    # read the configuration settings from a JSON file
    config = read_config("./config.json")

    # fetch data from pdf files and export it
    start = time.perf_counter()
    initial = fetch_terms_from_doi(source)
    export_data(initial, config.export_dir)
    result = fetch_citations_hence(initial)
    # result = fetch_terms_from_pdf_files(config)
    export_data(result, config.export_dir)
    elapsed = time.perf_counter() - start
    log_msg(f"\n[sciscraper]: Extraction finished in {elapsed} seconds.\n")


if __name__ == "__main__":
    main()
