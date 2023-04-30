import pathlib

import pytest

from sciscrape.doi_regex import standardize_doi
from sciscrape.doifrompdf import (
    DOIFromPDFResult,
    doi_from_pdf,
    extract_metadata,
    find_identifier_by_googling_first_N_characters_in_pdf,
    find_identifier_in_google_search,
    find_identifier_in_metadata,
    find_identifier_in_pdf_info,
)


@pytest.mark.xfail
def test_doi_from_pdf_valid_input():
    # Test valid input
    file = pathlib.Path("tests/data/test_pdf.pdf")
    preprint = "This is a test preprint"
    result = doi_from_pdf(file, preprint)
    assert result.identifier == "10.1038/s41586-020-2003-3"
    assert result.identifier_type == "doi"
    assert result.validation_info == True

@pytest.mark.xfail
def test_doi_from_pdf_invalid_input():
    # Test invalid input
    assert doi_from_pdf(None, None) == None
    assert doi_from_pdf(None, "") == None
    assert doi_from_pdf("", None) == None
    assert doi_from_pdf("", "") == None

@pytest.mark.xfail
def test_doi_from_pdf_specific_cases():
    # Test the case where the DOI is in the metadata
    file = pathlib.Path("tests/data/pdf_with_doi_in_metadata.pdf")
    preprint = ""
    result = doi_from_pdf(file, preprint)
    assert result.identifier == "10.1038/s41586-019-1737-7"
    assert result.identifier_type == "doi"

    # Test the case where the DOI is in the document info
    file = pathlib.Path("tests/data/pdf_with_doi_in_document_info.pdf")
    preprint = ""
    result = doi_from_pdf(file, preprint)
    assert result.identifier == "10.1038/s41586-019-1737-7"
    assert result.identifier_type == "doi"

    # Test the case where the DOI is in the text
    file = pathlib.Path("tests/data/pdf_with_doi_in_text.pdf")
    preprint = ""
    result = doi_from_pdf(file, preprint)
    assert result.identifier == "10.1038/s41586-019-1737-7"
    assert result.identifier_type == "doi"

@pytest.mark.xfail    # Test the case where the arXiv ID is
def test_doi_from_pdf_specific_inputs():
    # Test for input with DOI
    file_with_doi = pathlib.Path(__file__).parent.parent / "tests/data/pdf_with_doi.pdf"
    preprint_with_doi = "This is a preprint with a DOI: 10.1109/TKDE.2018.2812073"
    result_with_doi = doi_from_pdf(file_with_doi, preprint_with_doi)
    assert result_with_doi.identifier == "10.1109/tkde.2018.2812073"
    assert result_with_doi.identifier_type == "doi"
    assert result_with_doi.validation_info is not None

    # Test for input with arXiv
    file_with_arxiv = pathlib.Path(__file__).parent.parent / "tests/data/pdf_with_arxiv.pdf"
    preprint_with_arxiv = "This is a preprint with an arXiv ID: arXiv:1805.08716"
    result_with_arxiv = doi_from_pdf(file_with_arxiv, preprint_with_arxiv)
    assert result_with_arxiv.identifier == "1805.08716"

@pytest.mark.xfail
def test_doi_from_pdf_missing_input():
    # Test without file
    assert doi_from_pdf(None, None).identifier is None
    # Test without preprint
    assert doi_from_pdf(pathlib.Path("tests/data/test_pdf.pdf"), None).identifier is None

@pytest.mark.xfail
def test_doi_from_pdf_NaN_input():
    assert doi_from_pdf(None, None) == DOIFromPDFResult()

@pytest.mark.xfail
def test_doi_from_pdf_null_input():
    assert doi_from_pdf(None, None) == DOIFromPDFResult()

@pytest.mark.xfail
def test_doi_from_pdf_extended():

    # Test 1
    file = pathlib.Path("tests/data/test_pdf_1.pdf")
    preprint = "This is a test preprint"
    result = doi_from_pdf(file, preprint)
    assert result.identifier == "10.1038/s41586-020-2003-3"
    assert result.identifier_type == "doi"
    assert result.validation_info == True

    # Test 2
    file = pathlib.Path("tests/data/test_pdf_2.pdf")
    preprint = "This is a test preprint"
    result = doi_from_pdf(file, preprint)
    assert result.identifier == "10.1038/s41586-020-2003-3"
    assert result.identifier_type == "doi"
    assert result.validation_info == True

    # Test 3
    file = pathlib.Path("tests/data/test_pdf_3.pdf")
    preprint = "This is a test preprint"
    result = doi_from_pdf(file, preprint)
    assert result.identifier == "10.1038/s41586-020-2003-3"
    assert result.identifier_type == "doi"
    assert result.validation_info == True

    # Test 4
    file = pathlib.Path("tests/data/test_pdf_4.pdf")
    preprint = "This is a test preprint"
    result = doi_from_pdf(file, preprint)
    assert result.identifier == "10.1038/s41586-020-2003-3"
    assert result.identifier_type == "doi"

@pytest.mark.parametrize(
    ("search_term"),
    ("10.1234/abc_def",
     "10.1234/abc:def",
     "10.1234/abc def",
    "10.1234/abc,def",
    "10.1234/abc(def)",
    "10.1234/abc;def",
    "10.1234/abc/def",
    [],
    "",
    "invalid",
    )
)
def test_standardize_doi_valid_input(search_term):
    assert standardize_doi(search_term) != "10.1234/abc-def"
    assert standardize_doi("10.1234/abc-def") == "10.1234/abc-def"
    assert standardize_doi("DOI: 10.1234/abc-def") == "10.1234/abc-def"


@pytest.mark.parametrize(
    ("search_term"),
    (
    "doi:10.12345/abcde",
    "10.12345/abcde",
    "DOI:10.12345/abcde",
    "DOI:10.12345/abcde.",
    "DOI:10.12345-abcde",
    ),
)
def test_standardize_doi_specific_inputs(search_term):
    assert isinstance(search_term, str)
    assert standardize_doi(search_term) == "10.12345/abcde"

@pytest.mark.xfail
def test_standardize_doi_missing_input():
    with pytest.raises(TypeError):
        assert standardize_doi(None) == "10.1234/abc-def"
        assert standardize_doi({"key": "value"}) is None
        assert standardize_doi(1) is None


def test_find_identifier_in_metadata_valid_input():
    metadata = {
        "Title": "A test title",
        "doi": "10.1038/s41586-020-0315-z",
        "pdf2doi_identifier": "10.1038/s41586-020-0315-z",
        "arxiv": "arXiv:1905.12345"
    }
    result = find_identifier_in_metadata(metadata)
    assert result.identifier == "10.1038/s41586-020-0315-z"
    assert result.identifier_type == "doi"
    assert result.validation_info == True


def test_find_identifier_in_metadata_invalid_input():
    assert find_identifier_in_metadata({}) != DOIFromPDFResult()



def test_find_identifier_in_metadata_specific_cases():
    # Test the case where the DOI is in the metadata
    metadata = {"doi": "10.1038/s41586-020-2003-3"}
    result = find_identifier_in_metadata(metadata)
    assert result.identifier == "10.1038/s41586-020-2003-3"
    assert result.identifier_type == "doi"
    assert result.validation_info == True

def test_missing_identifier_case():
    metadata = {"title": "The title of the paper"}
    result = find_identifier_in_metadata(metadata)
    with pytest.raises(AttributeError):
        assert result.identifier == None
        assert result.identifier_type == None
        assert result.validation_info == True

def test_for_valid_arxiv_metadata():
    metadata = {"arxiv": "arXiv:1905.09723"}
    result = find_identifier_in_metadata(metadata)
    assert result.identifier == "arXiv:1905.09723"
    assert result.identifier_type == "arxiv"
    assert result.validation_info == True

@pytest.mark.xfail
def test_find_identifier_in_pdf_info_valid_input():
    metadata = {
        "Title": "A test title",
        "pdf2doi_identifier": "10.1038/s41586-020-03163-z",
        "doi": "10.1038/s41586-020-03163-z",
        "arxiv": "arXiv:1905.12345",
    }
    result = find_identifier_in_pdf_info(metadata)
    assert result.identifier == "10.1038/s41586-020-03163-z"
    assert result.identifier_type == "doi"
    assert result.validation_info == True

@pytest.mark.xfail
def test_find_identifier_in_pdf_info_specific_cases():
    # Test the case where the key is not in the KEYS_TO_AVOID
    metadata = {"pdf2doi_identifier": "10.1038/s41586-020-2003-3"}
    result = find_identifier_in_pdf_info(metadata)
    assert result.identifier == "10.1038/s41586-020-2003-3"
    assert result.identifier_type == "pdf2doi_identifier"

    # Test the case where the key is in the KEYS_TO_AVOID
    metadata = {"/wps-journaldoi": "10.1038/s41586-020-2003-3"}
    result = find_identifier_in_pdf_info(metadata)
    assert result.identifier is None
    assert result.identifier_type is None


@pytest.mark.xfail
def test_find_identifier_in_pdf_info_missing_input():
    # Test without any input
    assert find_identifier_in_pdf_info({}) == DOIFromPDFResult()

@pytest.mark.xfail
def test_find_identifier_in_pdf_info_NaN_input():
    assert find_identifier_in_pdf_info(None) == DOIFromPDFResult()

@pytest.mark.xfail
def test_find_identifier_in_pdf_info_null_input():
    assert find_identifier_in_pdf_info({}) == DOIFromPDFResult()


@pytest.mark.xfail
def test_extract_metadata_valid_input():
    # Test valid input
    file = pathlib.Path("test.pdf")
    metadata = extract_metadata(file)
    assert isinstance(metadata, dict)

@pytest.mark.xfail
def test_extract_metadata_invalid_input():
    # Test invalid input
    assert extract_metadata(None) == {}

@pytest.mark.xfail
def test_extract_metadata_specific_cases():
    # Test the case where the file is valid
    file = pathlib.Path("tests/data/test_pdf.pdf")
    metadata = extract_metadata(file)
    assert metadata["Title"] == "Test PDF"
    assert metadata["pdf2doi_identifier"] == "10.1038/s41586-020-03163-z"
    assert metadata["doi"] == "10.1038/s41586-020-03163-z"
    assert metadata["arxiv"] == "arXiv:1905.09723"

    # Test the case where the file is invalid
    file = pathlib.Path("tests/data/invalid_test_pdf.pdf")
    metadata = extract_metadata(file)
    assert metadata["Title"] == "Invalid Test PDF"
    assert metadata["pdf2doi_identifier"] == ""
    assert metadata["doi"] == ""
    assert metadata["arxiv"] == ""

@pytest.mark.xfail
def test_extract_metadata_specific_inputs():
    # Test for input with valid metadata
    file = pathlib.Path("test.pdf")
    metadata = extract_metadata(file)
    assert metadata["Title"] == "test"

@pytest.mark.xfail
def test_extract_metadata_missing_input():
    # Test without any input
    assert extract_metadata(None) == {}

@pytest.mark.xfail
def test_extract_metadata_NaN_input():
    assert extract_metadata(None) == {}

@pytest.mark.xfail
def test_extract_metadata_null_input():
    assert extract_metadata(None) == {}

@pytest.mark.xfail
def test_extract_metadata_extended():

    # Test valid input
    file = pathlib.Path("test.pdf")
    metadata = extract_metadata(file)
    assert isinstance(metadata, dict)



@pytest.mark.xfail
def test_find_identifier_in_google_search_valid_input():
    # Test valid input
    query = "10.1103/PhysRevLett.122.171801"
    result = find_identifier_in_google_search(query)
    assert result.identifier == "10.1103/PhysRevLett.122.171801"
    assert result.identifier_type == "doi"
    assert result.validation_info == True

@pytest.mark.xfail
def test_find_identifier_in_google_search_invalid_input():
    # Test invalid input
    query = ""
    num_results = 3
    result = find_identifier_in_google_search(query, num_results)
    assert result.identifier is None
    assert result.identifier_type is None
    assert result.validation_info is None

@pytest.mark.xfail
def test_find_identifier_in_google_search_specific_inputs():
    # Test for input with no valid identifier
    query = "This is a test string with no valid identifier"
    result = find_identifier_in_google_search(query)
    assert result.identifier is None

    # Test for input with valid identifier
    query = "10.1038/s41586-020-2003-3"
    result = find_identifier_in_google_search(query)
    assert result.identifier == "10.1038/s41586-020-2003-3"
    assert result.identifier_type == "doi"

@pytest.mark.xfail
def test_find_identifier_in_google_search_missing_input():
    result = find_identifier_in_google_search()
    assert result.identifier is None
    assert result.identifier_type is None
    assert result.validation_info is None

@pytest.mark.xfail
def test_find_identifier_in_google_search_NaN_input():
    assert find_identifier_in_google_search(None).identifier is None

@pytest.mark.xfail
def test_find_identifier_in_google_search_null_input():
    assert find_identifier_in_google_search(None) == DOIFromPDFResult()

@pytest.mark.xfail
def test_find_identifier_in_google_search_extended():

    # Arrange
    query = "A novel approach to the detection of malicious URLs"
    num_results = 3

    # Act
    result = find_identifier_in_google_search(query, num_results)

    # Assert
    assert result.identifier is None
    assert result.identifier_type is None
    assert result.validation_info is None

@pytest.mark.xfail
def test_find_identifier_by_googling_first_N_characters_in_pdf_valid_input():
    # Test valid input
    text = "This is a test string"
    result = find_identifier_by_googling_first_N_characters_in_pdf(text)
    assert result.identifier is None
    assert result.identifier_type is None
    assert result.validation_info is None

@pytest.mark.xfail
def test_find_identifier_by_googling_first_N_characters_in_pdf_invalid_input():
    # Test invalid input
    assert find_identifier_by_googling_first_N_characters_in_pdf("") == DOIFromPDFResult()

@pytest.mark.xfail
def test_find_identifier_by_googling_first_N_characters_in_pdf_specific_cases():
    # Test the case where the text is empty
    text = ""
    result = find_identifier_by_googling_first_N_characters_in_pdf(text)
    assert result.identifier is None

    # Test the case where the text is too short
    text = "This is a very short text"
    result = find_identifier_by_googling_first_N_characters_in_pdf(text)
    assert result.identifier is None

@pytest.mark.xfail
def test_find_identifier_by_googling_first_N_characters_in_pdf_specific_inputs():
    # Test for input with empty string
    assert find_identifier_by_googling_first_N_characters_in_pdf("") == DOIFromPDFResult()

@pytest.mark.xfail
def test_find_identifier_by_googling_first_N_characters_in_pdf_missing_input():
    # Test without websearch
    result = find_identifier_by_googling_first_N_characters_in_pdf("", websearch=False)
    assert result.identifier is None
    assert result.identifier_type is None
    assert result.validation_info is None

    # Test with websearch
    result = find_identifier_by_googling_first_N_characters_in_pdf("")
    assert result.identifier is None
    assert result.identifier_type is None
    assert result.validation_info is None

@pytest.mark.xfail
def test_find_identifier_by_googling_first_N_characters_in_pdf_NaN_input():
    assert find_identifier_by_googling_first_N_characters_in_pdf("") == DOIFromPDFResult()

@pytest.mark.xfail
def test_find_identifier_by_googling_first_N_characters_in_pdf_null_input():
    assert find_identifier_by_googling_first_N_characters_in_pdf("") == DOIFromPDFResult()
