import pathlib

import pytest

from sciscrape.doifrompdf import DOIFromPDFResult, doi_from_pdf


@pytest.mark.xfail
def test_doi_from_pdf_valid_input():
    # Test valid input
    file = pathlib.Path('tests/data/test_pdf.pdf')
    preprint = "This is a test preprint"
    result = doi_from_pdf(file, preprint)
    # TODO: Review values in assert statement
    assert result.identifier == '10.1038/s41586-020-2003-3'
    # TODO: Review values in assert statement
    assert result.identifier_type == 'doi'
    # TODO: Review values in assert statement
    assert result.validation_info == True

@pytest.mark.xfail
def test_doi_from_pdf_invalid_input():
    # Test invalid input
    # TODO: Review values in assert statement
    assert doi_from_pdf(None, None) == None
    # TODO: Review values in assert statement
    assert doi_from_pdf(None, "") == None
    # TODO: Review values in assert statement
    assert doi_from_pdf("", None) == None
    # TODO: Review values in assert statement
    assert doi_from_pdf("", "") == None

@pytest.mark.xfail
def test_doi_from_pdf_specific_cases():
    # Test the case where the DOI is in the metadata
    file = pathlib.Path('tests/data/pdf_with_doi_in_metadata.pdf')
    preprint = ""
    result = doi_from_pdf(file, preprint)
    # TODO: Review values in assert statement
    assert result.identifier == '10.1038/s41586-019-1737-7'
    # TODO: Review values in assert statement
    assert result.identifier_type == 'doi'

    # Test the case where the DOI is in the document info
    file = pathlib.Path('tests/data/pdf_with_doi_in_document_info.pdf')
    preprint = ""
    result = doi_from_pdf(file, preprint)
    # TODO: Review values in assert statement
    assert result.identifier == '10.1038/s41586-019-1737-7'
    # TODO: Review values in assert statement
    assert result.identifier_type == 'doi'

    # Test the case where the DOI is in the text
    file = pathlib.Path('tests/data/pdf_with_doi_in_text.pdf')
    preprint = ""
    result = doi_from_pdf(file, preprint)
    # TODO: Review values in assert statement
    assert result.identifier == '10.1038/s41586-019-1737-7'
    # TODO: Review values in assert statement
    assert result.identifier_type == 'doi'

@pytest.mark.xfail    # Test the case where the arXiv ID is
def test_doi_from_pdf_specific_inputs():
    # Test for input with DOI
    file_with_doi = pathlib.Path(__file__).parent.parent / 'tests/data/pdf_with_doi.pdf'
    preprint_with_doi = "This is a preprint with a DOI: 10.1109/TKDE.2018.2812073"
    result_with_doi = doi_from_pdf(file_with_doi, preprint_with_doi)
    # TODO: Review values in assert statement
    assert result_with_doi.identifier == "10.1109/tkde.2018.2812073"
    # TODO: Review values in assert statement
    assert result_with_doi.identifier_type == "doi"
    # TODO: Review values in assert statement
    assert result_with_doi.validation_info is not None

    # Test for input with arXiv
    file_with_arxiv = pathlib.Path(__file__).parent.parent / 'tests/data/pdf_with_arxiv.pdf'
    preprint_with_arxiv = "This is a preprint with an arXiv ID: arXiv:1805.08716"
    result_with_arxiv = doi_from_pdf(file_with_arxiv, preprint_with_arxiv)
    # TODO: Review values in assert statement
    assert result_with_arxiv.identifier == "1805.08716"

@pytest.mark.xfail
def test_doi_from_pdf_missing_input():
    # Test without file
    # TODO: Review values in assert statement
    assert doi_from_pdf(None, None).identifier is None
    # Test without preprint
    # TODO: Review values in assert statement
    assert doi_from_pdf(pathlib.Path('tests/data/test_pdf.pdf'), None).identifier is None

@pytest.mark.xfail
def test_doi_from_pdf_NaN_input():
    # Test NaN input
    # TODO: Review values in assert statement
    assert doi_from_pdf(None, None) == DOIFromPDFResult()

@pytest.mark.xfail
def test_doi_from_pdf_null_input():
    # Test null input
    # TODO: Review values in assert statement
    assert doi_from_pdf(None, None) == DOIFromPDFResult()

@pytest.mark.xfail
def test_doi_from_pdf_extended():

    # Test 1
    file = pathlib.Path('tests/data/test_pdf_1.pdf')
    preprint = 'This is a test preprint'
    result = doi_from_pdf(file, preprint)
    # TODO: Review values in assert statement
    assert result.identifier == '10.1038/s41586-020-2003-3'
    # TODO: Review values in assert statement
    assert result.identifier_type == 'doi'
    # TODO: Review values in assert statement
    assert result.validation_info == True

    # Test 2
    file = pathlib.Path('tests/data/test_pdf_2.pdf')
    preprint = 'This is a test preprint'
    result = doi_from_pdf(file, preprint)
    # TODO: Review values in assert statement
    assert result.identifier == '10.1038/s41586-020-2003-3'
    # TODO: Review values in assert statement
    assert result.identifier_type == 'doi'
    # TODO: Review values in assert statement
    assert result.validation_info == True

    # Test 3
    file = pathlib.Path('tests/data/test_pdf_3.pdf')
    preprint = 'This is a test preprint'
    result = doi_from_pdf(file, preprint)
    # TODO: Review values in assert statement
    assert result.identifier == '10.1038/s41586-020-2003-3'
    # TODO: Review values in assert statement
    assert result.identifier_type == 'doi'
    # TODO: Review values in assert statement
    assert result.validation_info == True

    # Test 4
    file = pathlib.Path('tests/data/test_pdf_4.pdf')
    preprint = 'This is a test preprint'
    result = doi_from_pdf(file, preprint)
    # TODO: Review values in assert statement
    assert result.identifier == '10.1038/s41586-020-2003-3'
    # TODO: Review values in assert statement
    assert result.identifier_type == 'doi'
    # TODO: Review values in assert statement
