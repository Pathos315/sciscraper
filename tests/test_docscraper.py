import pytest

from sciscrape.docscraper import DocumentResult


@pytest.mark.xfail
def test_docscraper(docscraper_summary, test_file_2):
    output_1 = docscraper_summary.obtain(test_file_2)
    assert isinstance(output_1, DocumentResult)
    assert isinstance(output_1.bycatch_freq, list)
    assert isinstance(output_1.target_freq, list)
    assert isinstance(output_1.wordscore, float)
