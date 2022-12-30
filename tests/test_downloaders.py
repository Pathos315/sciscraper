import re
from os import remove, path, getcwd
from unittest import mock
import pytest
from requests import Response
from sciscrape.downloaders import (
    DownloadReceipt,
    BulkPDFScraper,
    ImagesDownloader,
)
from sciscrape.config import config
from sciscrape.log import logger
from selectolax.parser import HTMLParser


def test_downloader_config(mock_bulkpdfscraper):
    assert mock_bulkpdfscraper.url == config.downloader_url
    assert path.exists(mock_bulkpdfscraper.export_dir)
    assert isinstance(mock_bulkpdfscraper.link_cleaning_pattern, re.Pattern)


@pytest.mark.xfail
def test_create_document(mock_bulkpdfscraper, mock_dirs):
    if path.exists("tests/test_dirs/temp_file.txt"):
        remove("tests/test_dirs/temp_file.txt")
    content = b"Pariatur labore duis do sint quis laborum fugiat. Do sit enim quis pariatur eiusmod. Eiusmod in laboris irure aliqua consequat nostrud quis.\n"
    file = mock_dirs / "test_example_1.txt"
    mock_bulkpdfscraper.create_document(file, content)
    with open(file, "wb") as btext:
        btext.write(content)
    with open(file, "rb") as text:
        output = text.read()
        assert output == content


@pytest.mark.parametrize(
    ("search_term", "expected"),
    (
        (
            "10.1038/s41586-020-2003-7",
            True,
        ),
        (None, False),
        (
            "",
            False,
        ),
    ),
)
def test_bulkpdf_receipt_validation(mock_bulkpdfscraper, search_term, expected):
    with mock.patch(
        "sciscrape.downloaders.BulkPDFScraper.obtain",
        return_value=DownloadReceipt(
            "test_downloader", success=expected, filepath="N/A"
        ),
        autospec=True,
    ):
        receipt = mock_bulkpdfscraper.obtain(search_term)
        assert isinstance(receipt, DownloadReceipt)
        assert receipt.success == expected
        assert receipt.filepath == "N/A"


@pytest.mark.xfail
def test_create_document_consistency(mock_bulkpdfscraper, mock_dirs):
    if path.exists("tests/test_dirs/temp_file.txt"):
        remove("tests/test_dirs/temp_file.txt")
    file = mock_dirs / "test_example_1.txt"
    current_dir = getcwd()
    mock_bulkpdfscraper.create_document(file, contents=b"hello\n")
    new_dir = getcwd()
    assert current_dir == new_dir


@pytest.mark.parametrize(
    ("download_link"),
    (
        (
            "location.href='/pdf/10.1038/s41586-020-2003-7",
            "location.href='/pdf/10.1038/s41586-020-2003-7.pdf",
            "location.href='/download/pdf/123456789.pdf",
        )
    ),
)
def test_valid_clean_link_with_regex(mock_bulkpdfscraper, download_link):
    link_match_object = mock_bulkpdfscraper.clean_link_with_regex(download_link)
    assert link_match_object.group(1) == "location.href='"
    assert link_match_object.group(2) == "/"


def test_invalid_clean_link_with_regex(mock_bulkpdfscraper):
    with pytest.raises(TypeError):
        link_match_object = mock_bulkpdfscraper.clean_link_with_regex(None)


def test_img_downloader_config(img_downloader):
    assert img_downloader.url == config.downloader_url
    assert img_downloader.export_dir == config.export_dir


def test_img_downloader_obtain(img_downloader):
    with mock.patch(
        "sciscrape.downloaders.ImagesDownloader.obtain",
        return_value=DownloadReceipt("", True),
        autospec=True,
    ):
        result = img_downloader.obtain("test")

    assert isinstance(result, DownloadReceipt)


@pytest.mark.parametrize(
    ("download_link", "expected"),
    (
        (
            "location.href='/downloads/2022-11-06/46/li2022.pdf?download=true",
            "https://sci-hub.se/downloads/2022-11-06/46/li2022.pdf?download=true",
        ),
        (None, None),
        (
            "location.href='//zero.sci-hub.se/7011/f4d76a25ca2ccd9ff38f46fd75b0b3bf/wang2017.pdf?download=true",
            "https://zero.sci-hub.se/7011/f4d76a25ca2ccd9ff38f46fd75b0b3bf/wang2017.pdf?download=true",
        ),
        (
            "location.href='/downloads/2020-01-28/9e/10.1016@B978-0-12-849867-5.00001-X.pdf?download=true",
            "https://sci-hub.se/downloads/2020-01-28/9e/10.1016@B978-0-12-849867-5.00001-X.pdf?download=true",
        ),
    ),
)
def test_format_download_link(mock_bulkpdfscraper, download_link, expected):
    output = mock_bulkpdfscraper.format_download_link(download_link)
    assert output == expected


@pytest.mark.parametrize(
    ("etag", "extension"),
    (
        ("173467321476c32789777643t732v73117888732476789764376", "png"),
        (None, "png"),
    ),
)
def test_img_downloader_etag(img_downloader, etag, extension):
    filename = img_downloader.format_filename(etag, extension)
    if etag is None:
        assert "__NaN__" in filename
    else:
        assert etag in filename
    assert extension in filename


def test_get_response(mock_response):
    downloader = BulkPDFScraper(url="https://httpstat.us/200")
    output = downloader.obtain(mock_response.text)
    assert isinstance(output, DownloadReceipt)
    assert output.success == False


def test_null_find_download_link(mock_bulkpdfscraper):
    assert mock_bulkpdfscraper.find_download_link("asfd") == None


@pytest.mark.parametrize(
    ("data"),
    (
        {"downloader": "test", "success": True, "filepath": "file/path.txt"},
        {"downloader": "test", "success": False, "filepath": "N/A"},
    ),
)
def test_download_creation(data):
    receipt = DownloadReceipt.from_dict(data)
    assert receipt.to_dict() == data


@pytest.mark.xfail
def test_create_mock_document():
    # create a mock object for the Downloader class
    downloader = mock.Mock()

    # create an instance of the DocumentCreator class

    # create a mock file and contents to pass to the create_document method
    mock_filename = "mock_file.txt"
    mock_contents = b"some mock contents"

    # create a mock context manager to simulate the change_dir function
    with mock.patch("builtins.open", mock.mock_open()) as mock_file:
        # call the create_document method
        downloader.create_document(filename=mock_filename, contents=mock_contents)

        # assert that the write method of the mock file object was called with the contents
        mock_file.return_value.write.assert_called_with(mock_contents)

        # assert that the remove method was called with the correct filepath
        remove.assert_called_with("temp_file.txt")


@pytest.mark.xfail
def test_create_document_writes_to_file():
    # create a mock object for the Downloader class
    downloader = mock.Mock()

    # create an instance of the DocumentCreator class
    creator = BulkPDFScraper(downloader)

    # create a mock file and contents to pass to the create_document method
    mock_filename = "temp_file.txt"
    mock_contents = b"some mock contents"

    # create a mock context manager to simulate the change_dir function
    with mock.patch("builtins.open", mock.mock_open()) as mock_file:
        # call the create_document method
        creator.create_document(mock_filename, mock_contents)

        # get the write method of the mock file object
        write_method = mock_file.return_value.write

        # assert that the write method was called once
        assert write_method.call_count == 1

        # get the call args of the write method
        call_args = write_method.call_args

        # assert that the write method was called with the contents
        assert call_args == ((mock_contents,),)


@pytest.mark.xfail
def test_download_paper():
    # create a mock object for the Downloader class
    downloader = mock.Mock()

    # create an instance of the DocumentCreator class
    creator = BulkPDFScraper(downloader)

    # create mock values for the paper_title and formatted_src arguments
    mock_paper_title = "mock_paper"
    mock_formatted_src = "http://mock.com/paper"

    # create a mock response object to simulate the request.get method
    mock_response = mock.Mock()

    # set the content attribute of the mock response object
    mock_response.content = b"some mock contents"

    # create a mock request object to simulate the client.get method
    mock_request = mock.Mock()

    # set the return value of the mock request object to the mock response object
    mock_request.return_value = mock_response

    # patch the requests.get method
    with mock.patch("requests.get", mock_request):
        # call the download_paper method
        receipt = creator.download_paper(mock_paper_title, mock_formatted_src)

        # assert that the download_paper method returned a DownloadReceipt object
        assert isinstance(receipt, DownloadReceipt)

        # assert that the DownloadReceipt object has the correct attributes
        assert isinstance(receipt.downloader, str)
        assert receipt.success == True
        assert receipt.filepath == f"{creator.export_dir}/{mock_paper_title}"


@pytest.mark.xfail
def test_download_image_invalid():
    mock_response = mock.Mock()
    # Test the case where the response is not 200
    mock_response.status_code = 404
    downloader = ImagesDownloader("http://mock.com/paper")
    expected = DownloadReceipt("ImagesDownloader")
    assert downloader.download_image("jpg", mock_response) == expected


@pytest.mark.xfail
def test_download_image_valid():
    # Test the case where the response is 200
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.headers["Etag"] = "12345"
    downloader = ImagesDownloader("https://www.google.com")
    expected = DownloadReceipt("ImagesDownloader", filepath="12345.jpg")
    assert downloader.download_image("jpg", mock_response) == expected


@pytest.mark.xfail
def test_find_download_link():
    instance = BulkPDFScraper(url="")
    search_text = "html text"
    mock_html_parser = mock.MagicMock(spec=HTMLParser)
    mock_html_parser.css_first.return_value.attributes = {"onclick": "download.pdf"}
    with (
        mock.patch("sciscrape.log.logger.debug") as mock_debug,
        mock.patch(
            "HTMLParser", return_value=mock_html_parser
        ) as mock_html_parser_constructor,
    ):
        result = instance.find_download_link(search_text)
        mock_html_parser_constructor.assert_called_once_with(search_text)
        mock_html_parser.css_first.assert_called_once_with(
            "#buttons button:nth-child(1)"
        )
        assert result == "download.pdf"
        mock_debug.assert_called_once_with("filename")


@pytest.mark.xfail
def test_image_downloader_obtain():
    instance = ImagesDownloader(url="")
    with (
        mock.patch("time.sleep") as mock_sleep,
        mock.patch(
            "sciscrape.downloaders.client.get",
            return_value=mock.MagicMock(spec=Response),
        ) as mock_client_get,
        mock.patch("sciscrape.log.logger.debug") as mock_logger_debug,
    ):
        search_text = "http://example.com/file.pdf"
        output = instance.obtain(search_text)
        mock_sleep.assert_called_once_with(instance.sleep_val)
        mock_client_get.assert_called_once_with(
            search_text, stream=True, allow_redirects=True
        )
        mock_logger_debug.assert_called_once_with(
            "response=%s, scraper=%s",
            repr(mock_client_get.return_value),
        )
        assert isinstance(output, DownloadReceipt)
