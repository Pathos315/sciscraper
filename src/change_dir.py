"""change_dir.py governs the file creation
processes for the sciscraper program.
"""
from __future__ import annotations

from contextlib import contextmanager
from os import chdir
from os import getcwd
from os import makedirs
from os import path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterator

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
