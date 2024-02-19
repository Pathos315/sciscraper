import json
from enum import Enum
from typing import Any
from unittest import mock

import pytest
import requests

from ..sciscrape.config import config
from ..sciscrape.webscrapers import (
    CitationScraper,
    DimensionsScraper,
    OverviewScraper,
    SemanticFigureScraper,
    WebScrapeResult,
)


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
def test_querystring_searchfield(scraper: DimensionsScraper, search_input, expected):
    querystring = scraper.create_querystring(search_input)
    assert querystring["search_field"] == expected
    assert isinstance(querystring, dict)


def test_scraper_inequality_by_kind():
    scraper_1 = DimensionsScraper(config.dimensions_ai_dataset_url, sleep_val=1)
    scraper_2 = CitationScraper(config.dimensions_ai_dataset_url, sleep_val=1)
    assert scraper_1 != scraper_2


def test_scraper_inequality_with_diff_urls():
    scraper_1 = DimensionsScraper(config.dimensions_ai_dataset_url)
    scraper_2 = DimensionsScraper(config.citation_crosscite_url)
    assert scraper_1 != scraper_2


def test_citation_querystring_creation():
    citation_scraper = CitationScraper(config.citation_crosscite_url, sleep_val=1)
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
    assert output.doi == input_query
    assert output.title == "Modeling Echo Chambers and Polarization Dynamics in Social Networks"


def test_obtain_returns_none(faulty_scraper: DimensionsScraper):
    input_query = "10.1103/physrevlett.124.048301"
    output = faulty_scraper.obtain(input_query)
    assert isinstance(output, WebScrapeResult) == False
    assert output == None


def test_get_extra_variables_getter_dict(scraper: DimensionsScraper, result_data: dict[str, Any]):
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


def test_get_extra_variables_key_error(scraper: DimensionsScraper):
    with pytest.raises(Exception):
        scraper.get_extra_variables("lorem", "ipsum")


@pytest.mark.skipif
def test_image_getter_sha(image_scraper: SemanticFigureScraper):
    with pytest.raises(json.decoder.JSONDecodeError):
        image_scraper.obtain("test")


def test_obtain_with_mock_patch(scraper: DimensionsScraper, result_data_as_class: WebScrapeResult):
    with mock.patch(
        "sciscrape.webscrapers.DimensionsScraper.obtain",
        return_value=result_data_as_class,
        autospec=True,
    ):
        result = scraper.obtain("test")
        assert isinstance(result, WebScrapeResult)
        assert result == result_data_as_class


@pytest.mark.skipif
def test_when_api_returns_no_content(scraper: DimensionsScraper):
    resp = scraper.get_docs("")
    assert resp.status_code == 200


@pytest.mark.skipif
def test_obtain_summary_text_not_found():
    scraper = OverviewScraper(url="https://app.dimensions.ai/details/publication")
    assert scraper.obtain("asdf") is None


@pytest.mark.skipif
def test_parse_html_tree_invalid_resp():
    # Test invalid response
    # TODO: Review values in assert statement
    assert SemanticFigureScraper(url="").parse_html_tree("") == None


@pytest.mark.skipif
def test_invalid_figure_obtain():
    with pytest.raises(requests.exceptions.MissingSchema):
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"results":[{"id":"12345"}]}'
        SemanticFigureScraper(url="").obtain("")


def test_get_invalid_doi():
    # Test invalid DOI
    scraper = DimensionsScraper(config.dimensions_ai_dataset_url)
    getter = CitationScraper(config.citation_crosscite_url, sleep_val=0.1)
    data = {"doi": "11.1038/s41586-019-1787-z"}
    # TODO: Review values in assert statement
    assert scraper.get_extra_variables(data, "doi", getter) is None


def test_null_extra_variables():
    getter = CitationScraper(config.citation_crosscite_url, sleep_val=0.1)
    scraper = DimensionsScraper(config.dimensions_ai_dataset_url)
    assert scraper.get_extra_variables({}, "", getter) == None


@pytest.mark.skipif
def test_missing_extra_variables():
    data = {"title": "test"}
    scraper = DimensionsScraper(config.dimensions_ai_dataset_url)
    getter = OverviewScraper(config.abstract_getting_url)
    query = "internal_id"
    assert scraper.get_extra_variables(data, query, getter) is None
