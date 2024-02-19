import re
from os import path
from typing import Literal
from unittest import mock

import pytest

from sciscrape.downloaders import BulkPDFScraper, ImagesDownloader

from sciscrape.config import config
from sciscrape.downloaders import DownloadReceipt


def test_downloader_config(mock_bulkpdfscraper: BulkPDFScraper):
    assert mock_bulkpdfscraper.url == config.downloader_url
    assert path.exists(mock_bulkpdfscraper.export_dir)
    assert isinstance(mock_bulkpdfscraper.link_cleaning_pattern, re.Pattern)


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
def test_bulkpdf_receipt_validation(mock_bulkpdfscraper: BulkPDFScraper, search_term, expected):
    with mock.patch(
        "sciscrape.downloaders.BulkPDFScraper.obtain",
        return_value=DownloadReceipt("test_downloader", success=expected, filepath="N/A"),
        autospec=True,
    ):
        receipt = mock_bulkpdfscraper.obtain(search_term)
        assert isinstance(receipt, DownloadReceipt)
        assert receipt.success == expected
        assert receipt.filepath == "N/A"


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
def test_valid_clean_link_with_regex(mock_bulkpdfscraper: BulkPDFScraper, download_link: Literal['location.href=\'/pdf/10.1038/s41586-020-2003-7', 'location.href=\'/pdf/10.1038/s41586-020-2003-7.pdf', 'location.href=\'/download/pdf/123456789.pdf']):
    link_match_object = mock_bulkpdfscraper.clean_link_with_regex(download_link)
    assert link_match_object.group(1) == "location.href='"
    assert link_match_object.group(2) == "/"


def test_img_downloader_obtain(img_downloader: ImagesDownloader):
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
def test_format_download_link(mock_bulkpdfscraper: BulkPDFScraper, download_link, expected):
    output = mock_bulkpdfscraper.format_download_link(download_link)
    assert output == expected