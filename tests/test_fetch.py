import logging
from typing import Callable
import numpy as np
import pandas as pd
import pytest

from sciscrape.docscraper import DocScraper
from sciscrape.downloaders import Downloader
from sciscrape.fetch import SciScraper, StagingFetcher, ScrapeFetcher
from sciscrape.factories import SCISCRAPERS, read_factory
from sciscrape.change_dir import change_dir
from sciscrape.webscrapers import WebScraper
from sciscrape.config import config
from unittest import mock
from sciscrape.log import logger


@pytest.mark.parametrize(
    ("key"), (("wordscore", "citations", "reference", "download", "images"))
)
def test_read_factory_input(monkeypatch: pytest.MonkeyPatch, key):
    monkeypatch.setattr("builtins.input", lambda _: key)
    output = read_factory()
    assert isinstance(output, SciScraper)
    assert isinstance(output.stager, StagingFetcher)
    assert isinstance(output.scraper, ScrapeFetcher)
    assert isinstance(output.scraper.scraper, (DocScraper, WebScraper, Downloader))


def test_faulty_factory_input(monkeypatch: pytest.MonkeyPatch):
    first = True
    input_calls: int = 0

    def myinp(_):
        nonlocal input_calls, first
        input_calls += 1
        if first:
            first = not first
            return "lisjdfklsdjlkfjdsklfjsd"
        return "citations"

    monkeypatch.setattr("builtins.input", myinp)
    output = read_factory()
    assert input_calls == 2
    assert isinstance(output, SciScraper)


def test_downcast_available_datetimes_validity():
    df = pd.DataFrame({"pub_date": ["2020-01-01", "2020-01-02", "2020-01-03"]})
    assert SciScraper.downcast_available_datetimes(df).dtype == "datetime64[ns]"


def test_null_datetimes_downcasting():
    df = pd.DataFrame({"pub_date": ["", "", ""]})
    assert SciScraper.downcast_available_datetimes(df).isnull().all()


def test_no_datetimes_downcasting():
    with pytest.raises(ValueError):
        df = pd.Series({"pub_date": ["a", "b", "c"]})
        SciScraper.downcast_available_datetimes(df).equals(df)


def test_empty_datetimes_downcasting():
    with pytest.raises(KeyError):
        df = pd.DataFrame()
        SciScraper.downcast_available_datetimes(df)


def test_NaN_datetimes_downcasting():
    # Test NaN values
    df = pd.DataFrame({"pub_date": [np.nan]})
    # TODO: Review values in assert statement
    assert SciScraper.downcast_available_datetimes(df).isnull().all()


def test_none_downcast_available_datetimes():
    df = pd.DataFrame({"pub_date": [None, None, None]})
    assert SciScraper.downcast_available_datetimes(df).isnull().all()



def test_fetch_serializerstrategy(fetch_scraper, mock_csv, mock_dataframe):
    with mock.patch(
        "sciscrape.fetch.ScrapeFetcher.fetch",
        return_value=mock_dataframe,
        autospec=True,
    ):

        assert isinstance(fetch_scraper.scraper.serializer, Callable)
        search_terms = fetch_scraper.scraper.serializer(mock_csv)
        assert isinstance(search_terms, list)
        output_a = fetch_scraper.scraper.fetch(search_terms)
        output_b = fetch_scraper.scraper(mock_csv)
        assert isinstance(output_a, pd.DataFrame)
        assert isinstance(output_b, pd.DataFrame)


def test_fetch(fetch_scraper, mock_csv):
    with mock.patch(
        "sciscrape.fetch.ScrapeFetcher.__call__",
        return_value=None,
        autospec=True,
    ):
        search_terms = fetch_scraper.scraper.serializer(mock_csv)
        assert isinstance(search_terms, list)
        output = fetch_scraper.scraper.fetch(search_terms)
        assert isinstance(output, pd.DataFrame)
        assert output.empty is False
        assert output.dtypes["title"] == "object"
        new_data = fetch_scraper.dataframe_casting(output)
        assert new_data.dtypes["title"] == "string"


def test_fetch_with_staged_reference():
    test_sciscraper = SCISCRAPERS["reference"]
    with mock.patch(
        "sciscrape.fetch.StagingFetcher.fetch_with_staged_reference",
        return_value=pd.DataFrame,
    ):
        terms = (
            ["a", "b", "c", "d", "e", "f"],
            ["1", "2", "3", "1", "2", "3"],
        )
        output = test_sciscraper.stager.fetch_with_staged_reference(terms)  # type: ignore
        assert output is not None


def test_invalid_dataframe_logging(caplog, mock_dataframe):
    with caplog.at_level(logging.INFO, logger="sciscraper"):
        SciScraper.dataframe_logging(mock_dataframe)
        for record in caplog.records:
            assert record.levelname != "CRITICAL"


def test_create_export_name():
    output = SciScraper.create_export_name()
    assert f"{config.today}_sciscraper_" in output


class TestClass:
    def set_logging(self, debug: bool) -> None:
        logger.setLevel(10) if debug else logger.setLevel(20)

    @classmethod
    def dataframe_logging(cls, dataframe: pd.DataFrame) -> None:
        pass

    @classmethod
    def create_export_name(cls) -> str:
        return "test_50.csv"

    @classmethod
    def export(cls, dataframe: pd.DataFrame, export_dir: str = "export") -> None:
        """Export data to the specified export directory."""
        cls.dataframe_logging(dataframe)
        export_name = cls.create_export_name()
        with change_dir(export_dir):
            logger.info("A spreadsheet was exported as %s.", export_name)
            dataframe.to_csv(export_name)


def test_export(mock_dataframe):
    with (
        mock.patch("sciscrape.log.logger.info") as mock_logger,
        mock.patch("pandas.DataFrame.to_csv") as mock_to_csv,
        mock.patch(
            "sciscrape.change_dir.change_dir", return_value=None
        ) as mock_change_dir,
    ):
        TestClass.export(mock_dataframe)
        mock_logger.assert_called_once_with(
            f"A spreadsheet was exported as {TestClass.create_export_name()}."
        )
        mock_to_csv.assert_called_once_with(TestClass.create_export_name())


def test_set_logging():
    with mock.patch.object(logger, "setLevel") as mock_set_level:
        instance = TestClass()
        instance.set_logging(True)
        mock_set_level.assert_called_once_with(10)
        instance.set_logging(False)
        mock_set_level.assert_called_with(20)


def test_fetch_with_staged_reference_tuple_of_lists():
    staged_terms = (["citation"], [])
    scraper = mock.Mock()
    df = StagingFetcher(scraper, stager=None).fetch_with_staged_reference(staged_terms)  # type: ignore
    assert df.empty


def test_fetch_with_staged_reference_empty_tuple():
    staged_terms = ([], [])
    scraper = mock.Mock()
    df = StagingFetcher(scraper, stager=None).fetch_with_staged_reference(staged_terms)  # type: ignore
    assert df.empty


@pytest.mark.parametrize(("debug", "expected"), ((True, 10), (False, 20)))
def test_set_logging_valid_input(debug, expected):
    # Test valid input
    test_sciscraper = SCISCRAPERS["reference"]
    test_sciscraper.set_logging(debug)
    assert test_sciscraper.logger.level == expected
    assert SciScraper.logger.level == expected
    assert SciScraper.logger.getEffectiveLevel() == expected


def test_export_invalid_input():
    test_sciscraper = SCISCRAPERS["reference"]
    with (
        pytest.raises(AttributeError),
        change_dir(config.export_dir),
    ):
        test_sciscraper.export(None)  # type: ignore
