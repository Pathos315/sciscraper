from __future__ import annotations

from os import getcwd
from typing import Literal

from src.change_dir import change_dir


def test_change_dir(mock_dirs: Literal["tests/test_dirs"]):
    initial_directory: str = getcwd()
    with change_dir(mock_dirs):
        new_directory: str = getcwd()
        assert initial_directory != new_directory
    final_directory = getcwd()
    assert initial_directory == final_directory
