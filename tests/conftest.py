import pytest
import pandas as pd

import requests
from requests import Response
from sciscrape.docscraper import DocScraper
from sciscrape.wordscore import RelevanceCalculator
from sciscrape.config import config
from sciscrape.downloaders import (
    BulkPDFScraper,
    ImagesDownloader,
)
from sciscrape.webscrapers import (
    DimensionsScraper,
    WebScrapeResult,
    SemanticFigureScraper,
)
import responses
from unittest import mock

# File Path Fixtures
@pytest.fixture()
def mock_dirs():
    return "tests/test_dirs"


@pytest.fixture()
def mock_csv():
    return "tests/test_dirs/test_example_file_1.csv"


@pytest.fixture()
def mock_txt():
    return "tests/test_dirs/test_file.txt"


@pytest.fixture(scope="function")
def mock_dataframe(mock_csv) -> pd.DataFrame:
    return pd.read_csv(mock_csv)


@pytest.fixture()
def test_file_1():
    with open("tests/test_dirs/test_example_1.txt", "r") as file_1:
        return str(file_1.readlines())


@pytest.fixture()
def test_file_2():
    with open("tests/test_dirs/test_example_2.txt", "r") as file_2:
        return str(file_2.readlines())


@pytest.fixture()
def test_pdf():
    return "tests/test_dirs/test_pdf_1.pdf"


@pytest.fixture
def prior_df():
    return pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})


@pytest.fixture
def staged_terms():
    return [1, 2, 3]


@pytest.fixture
def staged_tuple():
    return ([1, 2, 3], [4, 5, 6])


### Result Fixtures ###
@pytest.fixture()
def mock_response() -> Response:
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"results":[{"id":"12345"}]}'
    return response


@pytest.fixture()
def mock_request():
    # create a mock response object to simulate the request.get method
    mock_response = mock.Mock()

    mock_response.byte_content = b"some mock contents"

    mock_response.dict_content = b'{"results":[{"id":"12345"}]}'

    mock_response.status_code = 200

    # create a mock request object to simulate the client.get method
    mock_request = mock.Mock()

    # set the return value of the mock request object to the mock response object
    mock_request.return_value = mock_response


@pytest.fixture()
def wordscore_calc():
    return RelevanceCalculator(
        target_count=64,
        bycatch_count=32,
        total_length=2048,
        implicature_score=0.5,
    )


@pytest.fixture()
def wordscore_dict() -> dict[str, float | int]:
    return {
        "target_count": 64,
        "bycatch_count": 32,
        "total_length": 2048,
        "implicature_score": 0.5,
    }


@pytest.fixture()
def result_data():
    return {
        "title": "Lorem",
        "pub_date": "01/02/2033",
        "doi": "10.0000",
        "internal_id": "10001",
        "journal_title": "Ipsum Dolor",
        "times_cited": 5,
        "author_list": ["John", "Mark", "Lee"],
        "citations": ["0.0000", "1.0000", "2.0000", "3.0000"],
        "keywords": None,
        "figures": None,
        "biblio": None,
        "abstract": None,
    }


@pytest.fixture()
def result_data_as_class():
    return WebScrapeResult(
        title="Lorem",
        pub_date="01/02/2033",
        doi="10.0000",
        internal_id="10001",
        journal_title="Ipsum Dolor",
        times_cited=5,
        author_list=["John", "Mark", "Lee"],
        citations=["0.0000", "1.0000", "2.0000", "3.0000"],
        keywords=None,
        figures=None,
        biblio=None,
        abstract=None,
    )


@pytest.fixture()
def docscraper_summary():
    return DocScraper(config.target_words, config.bycatch_words, False)


@pytest.fixture()
def docscraper_pdf():
    return DocScraper(config.target_words, config.bycatch_words, True)


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture()
def scraper():
    return DimensionsScraper(config.dimensions_ai_dataset_url, sleep_val=0.5)


@pytest.fixture()
def faulty_scraper():
    return DimensionsScraper(url="https://httpstat.us/404")


@pytest.fixture()
def image_scraper():
    return SemanticFigureScraper(url="https://httpstat.us/200")


@pytest.fixture()
def faulty_image_scraper():
    return SemanticFigureScraper(url="https://httpstat.us/404")


@pytest.fixture()
def mock_bulkpdfscraper(mock_dirs):
    return BulkPDFScraper(
        config.downloader_url,
        sleep_val=0.5,
        export_dir=mock_dirs,
    )


@pytest.fixture()
def img_downloader():
    return ImagesDownloader(config.downloader_url, sleep_val=0.5)
