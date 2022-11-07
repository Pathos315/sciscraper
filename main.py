from time import perf_counter

from scrape.log import logger
from scrape.factories import read_factory, config
from scrape.utils import export_data

def main() -> None:
    """Main function."""
    start = perf_counter()
    sciscrape = read_factory(True)
    data = sciscrape.run(config.demo_dir)
    export_data(data, config.research_dir)
    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed:.2f} seconds.")
    
if __name__ == "__main__":
    main()