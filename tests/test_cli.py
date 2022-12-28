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


@pytest.mark.xfail
def test_main(monkeypatch: pytest.MonkeyPatch):
    from sciscrape.fetch import SciScraper

    file_path: str = "tests/test_dirs/test_example_file_1.csv"
    monkeypatch.setattr("builtins.input", lambda _: "wordscore")
    mock_parser = MagicMock(spec=argparse.ArgumentParser)
    mock_sciscrape = MagicMock(spec=SciScraper)

    with (
        patch(
            "sciscraper.scrape.factories.read_factory", return_value=mock_sciscrape
        ) as mock_factory,
        patch("sciscraper.scrape.log.logger.info") as mock_logs,
    ):
        mock_argv = ["-f", file_path, "-d", "-e", "-b", "-m"]
        main(mock_argv)
        mock_factory.assert_called_once_with()
        mock_sciscrape.assert_called_once_with(file_path, True, True)
        mock_logs.assert_called_once_with("Extraction finished in 0.00 seconds.")


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
def test_run_benchmark_creates_profile_stats(mock_sciscrape):
    # Set up mock objects
    mock_args = Mock(file="test.txt", export="csv", debug=True)

    # Call the function with the mock objects
    run_benchmark(mock_args, mock_sciscrape)

    # Assert that the Profile context manager was called and the stats were created
    mock_pr = Mock()
    with patch("profile.Profile", return_value=mock_pr) as mock_profile:
        mock_stats = Mock()
        with patch("pstats.Stats", return_value=mock_stats) as mock_stats_constructor:
            run_benchmark(mock_args, mock_sciscrape)
            mock_stats_constructor.assert_called_once()
            (mock_pr.__enter__).assert_called_once()
            (mock_pr.__exit__).assert_called_once()
            mock_profile.assert_called_once_with(mock_pr)


def test_run_benchmark_sorts_stats_by_time(mock_sciscrape, mock_stats):
    # Set up mock objects
    mock_args = Mock(file="test.txt", export="csv", debug=True)

    # Call the function with the mock objects
    run_benchmark(mock_args, mock_sciscrape)

    # Assert that the stats were sorted by time
    mock_pr = Mock()
    with patch("profile.Profile", return_value=mock_pr) as mock_profile:
        with patch("pstats.Stats", return_value=mock_stats) as mock_stats_constructor:
            run_benchmark(mock_args, mock_sciscrape)
            mock_stats.sort_stats.assert_called_once_with(pstats.SortKey.TIME)
            mock_stats_constructor.assert_called_once()


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
