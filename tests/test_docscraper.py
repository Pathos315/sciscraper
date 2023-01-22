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
    assert isinstance(output, list)


def test_extract_text_from_pdf_list_str(docscraper_pdf, test_pdf):
    output = docscraper_pdf.extract_text_from_pdf(test_pdf)
    assert isinstance(output, list)
    assert all(isinstance(item, str) for item in output)
