"""change_dir.py governs the file creation
processes for the sciscraper program.
"""
from contextlib import contextmanager
from os import chdir, getcwd, makedirs, path
from typing import Iterator

from pydantic import DirectoryPath


@contextmanager
def change_dir(destination: DirectoryPath) -> Iterator[None]:
    """Sets a destination for exported files."""
    cwd = getcwd()
    try:
        dest = path.realpath(destination)
        makedirs(dest, exist_ok=True)
        chdir(dest)
        yield
    finally:
        chdir(cwd)
