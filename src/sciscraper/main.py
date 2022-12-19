import argparse
from typing import Optional, Sequence
from time import perf_counter

from sciscraper.scrape.log import logger
from sciscraper.scrape.utils import run_benchmark
from sciscraper.scrape.factories import read_factory
from sciscraper.scrape.config import config


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Run function."""

    parser = argparse.ArgumentParser(
        prog=config.prog,
        usage="%(prog)s [options] filepath",
        description=config.description,
    )
    parser.add_argument(
        "-f",
        "--file",
        metavar="FILE",
        type=str,
        default=config.source_file,
        help="Specify the target file: default: %(default)s)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        default=True,
        action="store_true",
        help="Specify debug logging output: default: %(default)s)",
    )
    parser.add_argument(
        "-e",
        "--export",
        default=True,
        action="store_true",
        help="Specify if exporting dataframe\
            to .csv: default: %(default)s)",
    )
    parser.add_argument(
        "-b",
        "--benchmark",
        default=False,
        action="store_true",
        help="Specify if benchmarking is to be conducted: default: %(default)s)",
    )
    args = parser.parse_args(argv)

    start = perf_counter()
    sciscrape = read_factory()
    logger.debug(repr(sciscrape))
    logger.debug(repr(args.file))

    if args.benchmark:
        run_benchmark(args, sciscrape)
    else:
        sciscrape(args.file, args.export, args.debug)

    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
