"""A robust behavioral science paper analyzer and downloader.

By John Fallot <john.fallot@gmail.com>
"""

import argparse
from functools import partial
from typing import Optional, Sequence
from time import perf_counter

from sciscrape.log import logger
from sciscrape.profilers import (
    run_benchmark,
    run_memory_profiler,
    run_bytecode_profiler,
)
from sciscrape.factories import read_factory, SCISCRAPERS
from sciscrape.config import config


def main(argv: Optional[Sequence[str]] = None) -> None:
    """
    Entry point for the `sciscraper` application. Parses command line arguments and executes the appropriate actions.

    The function uses the `argparse` module to parse command line arguments passed in the `argv` parameter.
    The parsed arguments are used to determine the actions to be taken, which may include running the `sciscrape`
    function with the specified file and export options, running a benchmark on the `sciscrape` function, or
    conducting a memory profile of the `sciscrape` function.

    Parameters
    ---------
    argv:
    A sequence of strings representing the command line arguments. If not provided, the default value is
    `None`, in which case the `argv` list is constructed from `sys.argv`.

    Returns
    -------
    None
    """

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
        default=False,
        help="Specify debug logging output: default: %(default)s)",
    )
    parser.add_argument(
        "-e",
        "--export",
        default=True,
        help="Specify if exporting dataframe\
            to .csv: default: %(default)s)",
    )
    parser.add_argument(
        "-p",
        "--profilers",
        default=None,
        choices=(
            "benchmark",
            "memory",
            "bytecode",
        ),
        help="Specify if benchmarking is to be conducted: default: %(default)s)",
    )
    parser.add_argument(
        "-m",
        "--mode",
        default=None,
        type=str,
        choices=(
            "directory",
            "wordscore",
            "citations",
            "reference",
            "download",
            "images",
            "relevance",
        ),
        help="Specify the sciscraper to be used,\
            if None is provided, the user will be prompted\
            with an input: %(default)s)",
    )
    args = parser.parse_args(argv)

    start = perf_counter()
    sciscrape = read_factory() if args.mode is None else SCISCRAPERS[args.mode]
    logger.debug(repr(sciscrape))
    logger.debug(repr(args.file))

    profiler_dict = {
        "benchmark": partial(run_benchmark,args=args),
        "memory": partial(run_memory_profiler,args=args),
        "bytecode": run_bytecode_profiler,
    }

    profiler_dict[args.profilers](sciscrape) if args.profilers else sciscrape(
        args.file, args.export, args.debug
    )

    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
