from __future__ import annotations

from enum import Enum
from typing import Any
from unittest import mock

import pytest

from src.config import config
from src.webscrapers import CitationScraper
from src.webscrapers import DimensionsScraper
from src.webscrapers import WebScrapeResult


@pytest.mark.parametrize(
    ("search_input", "expected"),
    (
        ("10.1000/182", "doi"),
        ("apples", "text_search"),
        ("10.1000/185", "doi"),
        ("Don Quixote", "text_search"),
        ("12.1050/100", "text_search"),
        ("100.000", "text_search"),
    ),
)
def test_querystring_searchfield(
    scraper: DimensionsScraper, search_input, expected
):
    querystring = scraper.create_querystring(search_input)
    assert querystring["search_field"] == expected
    assert isinstance(querystring, dict)


def test_scraper_inequality_by_kind():
    scraper_1 = DimensionsScraper(
        config.dimensions_ai_dataset_url, sleep_val=1
    )
    scraper_2 = CitationScraper(config.dimensions_ai_dataset_url, sleep_val=1)
    assert scraper_1 != scraper_2


def test_scraper_inequality_with_diff_urls():
    scraper_1 = DimensionsScraper(config.dimensions_ai_dataset_url)
    scraper_2 = DimensionsScraper(config.citation_crosscite_url)
    assert scraper_1 != scraper_2


def test_citation_querystring_creation():
    citation_scraper = CitationScraper(
        config.citation_crosscite_url, sleep_val=1
    )
    output = citation_scraper.create_querystring("testing")
    assert isinstance(output, dict)
    assert isinstance(citation_scraper.lang, str)
    assert isinstance(citation_scraper.style, Enum)
    assert isinstance(citation_scraper.style.value, str)


def test_obtain_null_search_text(scraper: DimensionsScraper):
    with pytest.raises(AttributeError):
        scraper.obtain(None)


@pytest.mark.skipif
def test_obtain_search_data(scraper: DimensionsScraper):
    input_query = "10.1103/physrevlett.124.048301"
    output = scraper.obtain(input_query)
    assert isinstance(output, WebScrapeResult)
    assert output.doi is input_query
    assert (
        output.title
        == "Modeling Echo Chambers and Polarization Dynamics in Social Networks"
    )


def test_obtain_returns_none(faulty_scraper: DimensionsScraper):
    input_query = "10.1103/physrevlett.124.048301"
    output = faulty_scraper.obtain(input_query)
    assert isinstance(output, WebScrapeResult) is False
    assert output is None


def test_get_extra_variables_getter_dict(
    scraper: DimensionsScraper, result_data: dict[str, Any]
):
    expected = None
    sample_dict = {
        "biblio": (
            "doi",
            CitationScraper(config.citation_crosscite_url, sleep_val=0.1),
        )
    }
    for key, getter in sample_dict.items():
        assert isinstance(key, str)
        assert isinstance(getter, tuple)
        assert isinstance(getter[0], str)
        assert isinstance(getter[1], CitationScraper)

        output = scraper.get_extra_variables(result_data, getter[0], getter[1])
        assert output == expected


def test_obtain_with_mock_patch(
    scraper: DimensionsScraper, result_data_as_class: WebScrapeResult
):
    with mock.patch(
        "src.webscrapers.DimensionsScraper.obtain",
        return_value=result_data_as_class,
        autospec=True,
    ):
        result = scraper.obtain("test")
        assert isinstance(result, WebScrapeResult)
        assert result == result_data_as_class
