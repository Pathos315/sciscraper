import argparse
import pstats
import pytest
from src.main import main
from unittest.mock import Mock, patch, MagicMock
from sciscrape.profilers import run_benchmark


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_cli(capsys, option):
    try:
        main([option])
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "usage: sciscraper [options]" in output


@pytest.fixture
def mock_sciscrape():
    return MagicMock()


@pytest.fixture
def mock_profile():
    return MagicMock()


@pytest.fixture
def mock_stats():
    stats = MagicMock()
    stats.sort_stats = MagicMock()
    stats.print_stats = MagicMock()
    stats.dump_stats = MagicMock()
    return stats


def test_run_benchmark_calls_sciscrape_with_correct_arguments(mock_sciscrape):
    # Set up mock objects
    mock_args = Mock(file="test.txt", export="csv", debug=True)

    # Call the function with the mock objects
    run_benchmark(mock_args, mock_sciscrape)

    # Assert that the mock function was called with the correct arguments
    mock_sciscrape.assert_called_once_with("test.txt", "csv", True)


@pytest.mark.xfail
def test_main_parses_command_line_arguments():
    # Set up mock objects
    mock_argv = ["prog", "-f", "test.txt", "-d", "-e"]
    mock_args = Mock(file="test.txt", export=True, debug=True)

    # Call the function with the mock objects
    with patch(
        "argparse.ArgumentParser.parse_args", return_value=mock_args
    ) as mock_parse_args:
        main(mock_argv)

    # Assert that the parse_args method was called with the correct arguments
    mock_parse_args.assert_called_once_with(mock_argv)


@pytest.mark.xfail
def test_main_executes_sciscrape_function_with_correct_arguments():
    # Set up mock objects
    mock_argv = ["prog", "-f", "test.txt", "-d", "-e"]
    mock_args = Mock(file="test.txt", export=True, debug=True)
    mock_sciscrape = Mock()

    # Call the function with the mock objects
    with patch("argparse.ArgumentParser.parse_args", return_value=mock_args):
        main(mock_argv)
        assert __name__ == "__main__"

    # Assert that the mock function was called with the correct arguments
    mock_sciscrape.assert_called_once_with("test.txt", True, True)
