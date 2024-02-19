"""argsbuilder constructs the argparser for sciscraper,
for use in the `main` module.
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from typing import Sequence

from pydantic import FilePath

from .config import config
from .factories import SCISCRAPERS


def build_parser(argv: Sequence[str] | None) -> Namespace:
    """
    build_parser builds the argument parser for sciscraper.

    Args:
        argv (Sequence[str] | None): arguments passed in via the `main` method.

    Returns:
        Namespace: parsed arguments.
    """
    parser = ArgumentParser(
        prog=config.prog,
        usage="%(prog)s [options] filepath",
        description=config.description,
    )
    parser.add_argument(
        "-f",
        "--file",
        metavar="FILE",
        type=FilePath,
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
            [key for key, _ in SCISCRAPERS.items()]
        ),
        help="Specify the sciscraper to be used,\
            if None is provided, the user will be prompted\
            with an input: %(default)s)",
    )
    return parser.parse_args(argv)
