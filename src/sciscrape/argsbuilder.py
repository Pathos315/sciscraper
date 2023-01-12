r"""argsbuilder constructs the argparser for sciscraper,
for use in the `main` module.
"""

import argparse
from typing import Optional, Sequence
from sciscrape.config import config

def build_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    """
    build_args builds the argument parser for sciscraper.

    Args:
        argv (Optional[Sequence[str]]): arguments passed in via the `main` method.

    Returns:
        argparse.Namespace: parsed arguments.
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
    return parser.parse_args(argv)
