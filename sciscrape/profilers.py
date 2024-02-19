import dis
import pstats
import subprocess
import sys
from argparse import Namespace
from cProfile import Profile
from functools import partial

import memory_profiler
import psutil

from .config import config
from .fetch import SciScraper


def _kill(proc_pid: int) -> None:
    """Kill the current benchmark process with SIGKILL, pre-emptively checking whether PID has been reused."""
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


def run_benchmark(args: Namespace, sciscrape: SciScraper) -> None:
    """
    Run a benchmark on the given SciScraper instance by profiling its execution and printing the results.

    The benchmark is run by calling the `sciscrape` function with the given `args` and profiling its execution
    using the `Profile` context manager from the `profile` module. The resulting profile statistics are then
    sorted by time and printed, and the stats are also dumped to a file specified by `config.profiling_path`.
    Finally, the `snakeviz` module is used to visualize the profile stats in a web browser.

    Args:
        args (Namespace): An object containing the arguments for the `sciscrape` function.
        sciscrape (SciScraper): An instance of the `SciScraper` class to be benchmarked.

    Returns:
        None
    """
    with Profile() as pr:
        sciscrape(args.file)
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    stats.dump_stats(config.profiling_path)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "snakeviz",
            config.profiling_path,
        ],
        shell=True,
    )
    try:
        proc.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        _kill(proc.pid)


@memory_profiler.profile(precision=4)
def run_memory_profiler(args: Namespace, sciscrape: SciScraper) -> None:
    """Benchmark the line by line memory usage of the `sciscraper` program."""
    sciscrape(args.file)


def run_bytecode_profiler(sciscrape: SciScraper) -> None:
    """Reproduce the bytecode of the entire `sciscraper` program."""
    dis.dis(sciscrape.__call__)


def get_profiler(args: Namespace, sciscrape: SciScraper) -> None:
    profiler_dict = {
        "benchmark": partial(run_benchmark, args=args),
        "memory": partial(run_memory_profiler, args=args),
        "bytecode": run_bytecode_profiler,
    }
    profiler_dict.get(args.profilers, sciscrape(args.file))
