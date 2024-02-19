import logging
from typing import Literal
from unittest import mock

import numpy as np
import pandas as pd
import pytest

from ..sciscrape.change_dir import change_dir
from ..sciscrape.docscraper import DocScraper
from ..sciscrape.downloaders import Downloader
from ..sciscrape.factories import SCISCRAPERS, read_factory
from ..sciscrape.fetch import SciScraper, ScrapeFetcher, StagingFetcher
from ..sciscrape.log import logger
from ..sciscrape.webscrapers import WebScraper


@pytest.mark.parametrize(("key"), (("wordscore", "citations")))
def test_read_factory_input(monkeypatch: pytest.MonkeyPatch, key: Literal['wordscore', 'citations']):
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


@pytest.mark.skip
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


def test_invalid_dataframe_logging(caplog: pytest.LogCaptureFixture, mock_dataframe: pd.DataFrame):
    with caplog.at_level(logging.INFO, logger="sciscraper"):
        SciScraper.dataframe_logging(mock_dataframe)
        for record in caplog.records:
            assert record.levelname != "CRITICAL"


class TestClass:
    def set_logging(self, debug: bool) -> None:
        logger.setLevel(10) if debug else logger.setLevel(20)

    @staticmethod
    def dataframe_logging(dataframe: pd.DataFrame) -> None:
        pass

    @staticmethod
    def create_export_name() -> str:
        return "test_50.csv"

    @staticmethod
    def export(dataframe: pd.DataFrame, export_dir: str = "export") -> None:
        """Export data to the specified export directory."""
        TestClass.dataframe_logging(dataframe)
        export_name = TestClass.create_export_name()
        with change_dir(export_dir):
            logger.info("A spreadsheet was exported as %s.", export_name)
            dataframe.to_csv(export_name)


def test_export(mock_dataframe: pd.DataFrame):
    with (mock.patch("pandas.DataFrame.to_csv") as mock_to_csv,):
        TestClass.export(mock_dataframe)
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
    assert not df.empty


def test_fetch_with_staged_reference_empty_tuple():
    staged_terms = ([], [])
    scraper = mock.Mock()
    df = StagingFetcher(scraper, stager=None).fetch_with_staged_reference(staged_terms)  # type: ignore
    assert df.empty

