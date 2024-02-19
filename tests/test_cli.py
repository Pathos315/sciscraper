from typing import Literal

import pytest

from ..main import main


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_cli(capsys: pytest.CaptureFixture[str], option: Literal['-h', '--help']):
    try:
        main([option])
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "usage: sciscraper [options]" in output
