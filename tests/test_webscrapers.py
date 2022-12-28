from enum import Enum
import json
import pytest
from unittest import mock
import requests
import responses
from sciscrape.webscrapers import (
    DimensionsScraper,
    CitationScraper,
    OverviewScraper,
    WebScrapeResult,
    SemanticFigureScraper,
)
from sciscrape.config import config


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
def test_querystring_searchfield(scraper, search_input, expected):
    querystring = scraper.create_querystring(search_input)
    assert querystring["search_field"] == expected
    assert isinstance(querystring, dict)


def test_scraper_inequality_by_kind():
    scraper_1 = DimensionsScraper(config.dimensions_ai_dataset_url)
    scraper_2 = CitationScraper(config.dimensions_ai_dataset_url)
    assert scraper_1 != scraper_2


def test_scraper_inequality_with_diff_urls():
    scraper_1 = DimensionsScraper(config.dimensions_ai_dataset_url)
    scraper_2 = DimensionsScraper(config.citation_crosscite_url)
    assert scraper_1 != scraper_2


@pytest.mark.xfail
def test_scraper_result_creation(result_data):
    scrape_result = WebScrapeResult.from_dict(result_data)
    assert scrape_result.to_dict() == result_data


def test_semantic_querystring_creation():
    output = SemanticFigureScraper(config.semantic_scholar_url_stub).create_querystring(
        "testing"
    )
    assert isinstance(output, dict)


def test_citation_querystring_creation():
    citation_scraper = CitationScraper(config.citation_crosscite_url)
    output = citation_scraper.create_querystring("testing")
    assert isinstance(output, dict)
    assert isinstance(citation_scraper.lang, str)
    assert isinstance(citation_scraper.style, Enum)
    assert isinstance(citation_scraper.style.value, str)


def test_obtain_null_search_text(scraper):
    with pytest.raises(AttributeError):
        scraper.obtain(None)


def test_obtain_search_data(scraper):
    input_query = "10.1103/physrevlett.124.048301"
    output = scraper.obtain(input_query)
    assert isinstance(output, WebScrapeResult)
    assert output.doi == input_query
    assert (
        output.title
        == "Modeling Echo Chambers and Polarization Dynamics in Social Networks"
    )


@pytest.mark.xfail
def test_obtain_returns_none(faulty_scraper):
    input_query = "10.1103/physrevlett.124.048301"
    output = faulty_scraper.obtain(input_query)
    assert isinstance(output, WebScrapeResult) == False
    assert output == None


def test_get_extra_variables_getter_dict(scraper, result_data):
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


def test_get_extra_variables_key_error(scraper):
    with pytest.raises(Exception):
        scraper.get_extra_variables("lorem", "ipsum")


def test_image_getter_sha(image_scraper):
    with pytest.raises(json.decoder.JSONDecodeError):
        image_scraper.obtain("test")


@pytest.mark.xfail
def test_image_getter_faulty_sha(faulty_image_scraper):
    output = faulty_image_scraper.obtain("test")
    assert output == None
    assert faulty_image_scraper.get_semantic_images("test") == None


@pytest.mark.parametrize(
    ("url"),
    (
        (config.dimensions_ai_dataset_url),
        (config.citation_crosscite_url),
        (config.semantic_scholar_url_stub),
        (config.downloader_url),
    ),
)
@responses.activate
def test_obtain_status_codes(url):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            url,
            body="{}",
            status=200,
            content_type="application/json",
        )
        resp = requests.get(url)
        assert resp.status_code == 200


def test_obtain_with_mock_patch(scraper, result_data_as_class):
    with mock.patch(
        "sciscrape.webscrapers.DimensionsScraper.obtain",
        return_value=result_data_as_class,
        autospec=True,
    ):
        result = scraper.obtain("test")
        assert isinstance(result, WebScrapeResult)
        assert result == result_data_as_class


def test_when_api_returns_no_content(scraper):
    resp = scraper.get_docs("")
    assert resp.status_code == 200


def test_obtain_summary_text_not_found():
    scraper = OverviewScraper(url="https://app.dimensions.ai/details/publication")
    assert scraper.obtain("asdf") is None


@pytest.mark.xfail
def test_get_semantic_images():
    # Test valid paper ID
    # TODO: Review values in assert statement
    assert SemanticFigureScraper(url="").get_semantic_images("a9b8c7d6e5f4g3h2i1j0")


def test_parse_html_tree_invalid_resp():
    # Test invalid response
    # TODO: Review values in assert statement
    assert SemanticFigureScraper(url="").parse_html_tree("") == None


def test_get_paper_id_valid():
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"results":[{"id":"12345"}]}'
    assert (
        SemanticFigureScraper.get_paper_id(SemanticFigureScraper(url=""), response.text)
        == "12345"
    )


def test_valid_figure_obtain():
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"results":[{"id":"12345"}]}'
    assert SemanticFigureScraper(url="https://httpstatus.io/").obtain("") == None


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


def test_missing_extra_variables():
    data = {"title": "test"}
    scraper = DimensionsScraper(config.dimensions_ai_dataset_url)
    getter = OverviewScraper(config.abstract_getting_url)
    query = "internal_id"
    assert scraper.get_extra_variables(data, query, getter) is None


def test_get_invalid_paper_id():
    response_text = '{"results": []}'
    assert SemanticFigureScraper(url="").get_paper_id(response_text) is None


def test_get_null_paper_id():
    with pytest.raises(KeyError):
        assert SemanticFigureScraper(url="").get_paper_id("{}") == None
