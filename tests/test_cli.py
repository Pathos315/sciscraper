from __future__ import annotations
from argparse import Namespace

import contextlib
import logging

from typing import Literal
from unittest.mock import Mock

import pytest

from main import main
from src.profilers import get_profiler


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_cli(
    capsys: pytest.CaptureFixture[str], option: Literal["-h", "--help"]
) -> None:
    with contextlib.suppress(SystemExit):
        main([option])
    output = capsys.readouterr().out
    assert "usage: sciscraper [options]" in output
