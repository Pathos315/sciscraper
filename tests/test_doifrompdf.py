from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import pdfplumber
import pytest
from feedparser import FeedParserDict
from googlesearch import search
from pydantic import FilePath

from src.doi_regex import IDENTIFIER_TYPES
from src.doifrompdf import (
    doi_from_pdf,
    find_identifier_by_googling_first_n_characters_in_pdf,
    find_identifier_in_google_search,
    find_identifier_in_metadata,
    find_identifier_in_pdf_info,
    find_identifier_in_text,
)
from src.log import logger
from src.webscrapers import client


@pytest.fixture
def file_path() -> FilePath:
    return "tests/data/sample.pdf"  # type: ignore


@pytest.fixture
def preprint() -> str:
    return "1234.5678"


@pytest.mark.xfail
def test_doi_from_pdf(file_path: FilePath, preprint: str) -> None:
    metadata = {"Title": "Test Title"}
    result = doi_from_pdf(file_path, preprint)
    assert result is not None
    assert result.identifier == "10.1234/1234.5678"
    assert result.identifier_type == "doi"


@pytest.mark.xfail
def test_doi_from_pdf_no_match(file_path: FilePath, preprint: str) -> None:
    result = doi_from_pdf(file_path, "12345678")
    assert result is None


@pytest.mark.xfail
def test_extract_metadata(file_path: FilePath) -> None:
    with pdfplumber.open(file_path) as pdf:
        metadata = pdf.metadata
        assert metadata == {"Title": "Test Title"}


def test_find_identifier_in_metadata(file_path: FilePath) -> None:
    metadata = {"doi": "10.1234/1234.5678", "Title": "Test Title"}
    result = find_identifier_in_metadata(metadata)
    assert result is not None
    assert result.identifier == "10.1234/1234.5678"
    assert result.identifier_type == "doi"


@pytest.mark.xfail
def test_find_identifier_in_metadata_no_match(file_path: FilePath) -> None:
    metadata = {"arxiv": "1234.5678", "Title": "Test Title"}
    result = find_identifier_in_metadata(metadata)
    assert result is None


@pytest.mark.xfail
def test_find_identifier_in_pdf_info(file_path: FilePath) -> None:
    metadata = {
        "/Title": "Test Title",
        "/wps-journaldoi": "10.1234/1234.5678",
    }
    result = find_identifier_in_pdf_info(metadata)
    assert result is not None
    assert result.identifier == "10.1234/1234.5678"
    assert result.identifier_type == "doi"


@pytest.mark.xfail
def test_find_identifier_in_pdf_info_no_match(file_path: FilePath) -> None:
    metadata = {"/Title": "Test Title"}
    result = find_identifier_in_pdf_info(metadata)
    assert result is None


@pytest.mark.xfail
def test_find_identifier_in_text(file_path: FilePath) -> None:
    text = "This is a test text with DOI: 10.1234/1234.5678"
    result = find_identifier_in_text(text)
    assert result is not None
    assert result.identifier == "10.1234/1234.5678"
    assert result.identifier_type == "doi"


@pytest.mark.xfail
def test_find_identifier_in_text_no_match(file_path: FilePath) -> None:
    text = "This is a test text with no DOI."
    result = find_identifier_in_text(text)
    assert result is None


@pytest.mark.xfail
def test_find_identifier_by_googling_first_n_characters_in_pdf(
    file_path: FilePath,
) -> None:
    text = "This is a test text with DOI: 10.1234/1234.5678"
    result = find_identifier_by_googling_first_n_characters_in_pdf(text)
    assert result is not None
    assert result.identifier == "10.1234/1234.5678"
    assert result.identifier_type == "doi"


@pytest.mark.xfail
def test_find_identifier_by_googling_first_n_characters_in_pdf_no_match(
    file_path: FilePath,
) -> None:
    text = "This is a test text with no DOI."
    result = find_identifier_by_googling_first_n_characters_in_pdf(text)
    assert result is None


@pytest.mark.xfail
def test_find_identifier_in_google_search(file_path: FilePath) -> None:
    result = find_identifier_in_google_search("test")
    assert result is None
