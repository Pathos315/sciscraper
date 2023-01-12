"""A robust behavioral science paper analyzer and downloader.

By John Fallot <john.fallot@gmail.com>
"""

from argparse import Namespace
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
from sciscrape.argsbuilder import build_args


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
    start = perf_counter()
    args: Namespace = build_args(argv)

    sciscrape = read_factory() if args.mode is None else SCISCRAPERS[args.mode]
    logger.debug(repr(sciscrape))
    logger.debug(repr(args.file))

    profiler_dict = {
        "benchmark": partial(run_benchmark, args=args),
        "memory": partial(run_memory_profiler, args=args),
        "bytecode": run_bytecode_profiler,
    }

    profiler_dict[args.profilers](sciscrape) if args.profilers else sciscrape(
        args.file,
        args.export,
        args.debug,
    )

    elapsed = perf_counter() - start
    logger.info(f"Extraction finished in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
