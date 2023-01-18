from typing import Generator

import pytest

from sciscrape.docscraper import DocumentResult


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
