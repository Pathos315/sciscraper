"""
Performance profiling utilities for the sciscraper application.

This module provides functions for profiling execution time, memory usage,
and bytecode of the application.
"""

from __future__ import annotations

import dis
import pstats
import subprocess
import sys
from cProfile import Profile
from functools import partial, wraps
from time import perf_counter
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import memory_profiler
import psutil

from src.config import config
from src.log import logger

if TYPE_CHECKING:
    from argparse import Namespace

    from src.fetch import SciScraper

# Type variable for generic functions
T = TypeVar("T")


def _kill(proc_pid: int) -> None:
    """
    Kill a process and all its children.

    Args:
        proc_pid: Process ID of the process to be killed
    """
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


def run_benchmark(args: Namespace, sciscrape: SciScraper) -> None:
    """
    Profile the execution of a function using cProfile and visualize the results.

    The benchmark runs the `sciscrape` function with the given `args` and profiles
    its execution using the `Profile` context manager. The profile statistics are
    sorted by time, printed to the console, and saved to a file. The `snakeviz`
    module is then used to visualize the results in a web browser.

    Args:
        args: An object containing the arguments for the `sciscrape` function
        sciscrape: An instance of the `SciScraper` class to be benchmarked
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


@memory_profiler.profile(precision=4)  # type: ignore[misc]
def run_memory_profiler(args: Namespace, sciscrape: SciScraper) -> None:
    """
    Profile the memory usage of a function using memory_profiler.

    This function uses the `memory_profiler` decorator to track the memory
    usage of the `sciscrape` function line by line.

    Args:
        args: An object containing the arguments for the `sciscrape` function
        sciscrape: An instance of the `SciScraper` class to be profiled
    """
    sciscrape(args.file)


def run_bytecode_profiler(sciscrape: SciScraper) -> None:
    """
    Display the bytecode of a function.

    This function uses the `dis` module to disassemble the bytecode of the
    `__call__` method of the `sciscrape` object.

    Args:
        sciscrape: An instance of the `SciScraper` class whose bytecode will be displayed
    """
    dis.dis(sciscrape.__call__)


def get_profiler(args: Namespace, sciscrape: SciScraper) -> None:
    """
    Run the appropriate profiler based on the arguments or execute the function directly.

    This function selects the appropriate profiler based on the `args.profilers` attribute.
    If `args.profilers` is one of "benchmark", "memory", or "bytecode", the corresponding
    profiler function is called. Otherwise, the `sciscrape` function is called directly
    with `args.file`.

    Args:
        args: The arguments passed to the script, containing `profilers` and `file` attributes
        sciscrape: The `SciScraper` instance to be profiled or executed
    """
    profiler_dict = {
        "benchmark": partial(run_benchmark, args=args),
        "memory": partial(run_memory_profiler, args=args),
        "bytecode": run_bytecode_profiler,
    }

    # Get the profiler function or execute sciscrape directly
    profiler_func = profiler_dict.get(args.profilers)
    if profiler_func:
        profiler_func(sciscrape)
    else:
        sciscrape(args.file)


def get_time(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to time a function's execution.

    This decorator wraps a function to measure and log the time it takes to execute.
    It uses `perf_counter` for high-precision timing.

    Args:
        func: The function to be timed

    Returns:
        A wrapped function that logs execution time and returns the original result
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Note that timing your code once isn't the most reliable option
        # for timing your code. Look into the timeit module for more accurate
        # timing.
        start_time: float = perf_counter()
        result: T = func(*args, **kwargs)
        end_time: float = perf_counter()

        logger.debug(
            f'"{func.__name__}()" took {end_time - start_time:.2f} seconds to execute'
        )
        return result

    return wrapper
