from __future__ import annotations

from enum import Enum
from typing import Any
from unittest import mock

import pytest

from src.config import config
from src.webscrapers import CitationScraper, GoogleScholarScraper
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


@pytest.mark.skip
def test_google_scholar_scraper():
    scraper = GoogleScholarScraper(
        url="https://scholar.google.com/scholar",
        sleep_val=1.0,
        start_year=2022,
        end_year=2022,
        publication_type="all",
        num_articles=2,
    )
    search_text = "10.1007/s42979-022-00422-4"
    result = next(scraper.obtain(search_text))
    if result:
        assert isinstance(result, WebScrapeResult) == True
        assert (
            result.title
            == "A Unified Framework for Federated Learning with Heterogeneous Data"
        )
        assert result.pub_date == "2022"
        assert result.doi == "10.1007/s42979-022-00422-4"
        assert result.internal_id == "all"
        assert result.abstract == "N/A"
        assert result.times_cited == 0
        assert result.journal_title == None
        assert result.keywords == ["10.1007/s42979-022-00422-4"]
        assert result.figures == None
        assert result.biblio == None
