import sys

# import dis
from cProfile import Profile
import pstats

from subprocess import Popen
from sciscrape.config import config
from sciscrape.fetch import SciScraper

from memory_profiler import profile


def run_benchmark(args, sciscrape: SciScraper) -> None:
    """
    Run a benchmark on the given SciScraper instance by profiling its execution and printing the results.

    The benchmark is run by calling the `sciscrape` function with the given `args` and profiling its execution
    using the `Profile` context manager from the `profile` module. The resulting profile statistics are then
    sorted by time and printed, and the stats are also dumped to a file specified by `config.profiling_path`.
    Finally, the `snakeviz` module is used to visualize the profile stats in a web browser.

    Parameters
    ---------
    args:
        An object containing the arguments for the `sciscrape` function.
    sciscrape:
        An instance of the `SciScraper` class to be benchmarked.

    Returns
    -------
        None
    """
    with Profile() as pr:
        sciscrape(args.file, args.export, args.debug)
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    stats.dump_stats(config.profiling_path)
    Popen([sys.executable, "-m", "snakeviz", config.profiling_path])


@profile(precision=4)
def run_memory_profiler(args, sciscrape: SciScraper) -> None:
    sciscrape(args.file, args.export, args.debug)


"""
TODO: def run_disassembler(args, sciscrape: SciScraper) -> None:
    dis.dis(sciscrape(args.file, args.export, args.debug))
"""
