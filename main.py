from time import perf_counter

from scrape.config import read_config
from scrape.fetch import run
from scrape.log import logger
from scrape.utils import export_data

config = read_config("./config.json")


def main() -> None:
    """Main function."""
    start = perf_counter()
    output = run("doi", target=config.test_src)
    export_data(output, config.export_dir)
    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed} seconds.")


if __name__ == "__main__":
    main()
