from unittest.mock import MagicMock, Mock, patch

import pytest

from main import main


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_cli(capsys, option):
    try:
        main([option])
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "usage: sciscraper [options]" in output
