from __future__ import annotations

import contextlib

from typing import Literal

import pytest

from main import main


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_cli(
    capsys: pytest.CaptureFixture[str], option: Literal["-h", "--help"]
) -> None:
    with contextlib.suppress(SystemExit):
        main([option])
    output = capsys.readouterr().out
    assert "usage: sciscraper [options]" in output
