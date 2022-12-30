from typing import Generator
import pytest
from sciscrape.docscraper import DocumentResult, TLDRScraper

@pytest.mark.xfail
def test_docscraper(docscraper_summary, test_file_2):
    output_1 = docscraper_summary.obtain(test_file_2)
    assert isinstance(output_1, DocumentResult)
    assert isinstance(output_1.bycatch_freq, list)
    assert isinstance(output_1.target_freq, list)
    assert isinstance(output_1.wordscore, float)


def test_extract_text_from_summary(docscraper_summary, test_file_1):
    output = docscraper_summary.extract_text_from_summary(test_file_1)
    for actual in output:
        assert isinstance(actual, list)


def test_extract_text_from_pdf(docscraper_pdf, test_pdf):
    output = docscraper_pdf.extract_text_from_pdf(test_pdf)
    assert isinstance(output, Generator)
    for item in output:
        assert isinstance(item, list)
        assert len(item) != 1
        assert all(isinstance(subitem, str) for subitem in item)


def test_navigate_api_valid_input():
    # Test valid input
    docs = [{"generated_text": "This is a test."}]
    # TODO: Review values in assert statement
    assert TLDRScraper("").navigate_api(docs) == "This is a test."

    # Test the case where the API returns a list of lists of lists


def test_navigate_api_specific_inputs():
    # Test for input with no "generated_text"
    with pytest.raises(TypeError):
        docs = [{"foo": "bar"}]
        TLDRScraper().navigate_api(docs) == "N/A"  # type: ignore


def test_navigate_api_missing_input():
    # Test without input
    docs = [{"generated_text": "This is a test"}]
    tldr = TLDRScraper(
        url="https://api-inference.huggingface.co/models/lrakotoson/scitldr-catts-xsum-ao",
        sleep_val=0.2,
    ).navigate_api(docs)
    # TODO: Review values in assert statement
    assert tldr == "This is a test"


def test_navigate_api_NaN_input():
    # Test NaN input
    docs = [{"generated_text": "N/A"}]
    # TODO: Review values in assert statement
    assert TLDRScraper("").navigate_api(docs) == "N/A"
