from __future__ import annotations

import re
from dataclasses import dataclass

import pdfplumber
from feedparser import FeedParserDict
from feedparser import parse as feedparse
from googlesearch import search
from pydantic import FilePath

from sciscrape.doi_regex import IDENTIFIER_PATTERNS, standardize_doi
from sciscrape.log import logger
from sciscrape.webscrapers import client


@dataclass(frozen=True)
class DOIFromPDFResult:
    identifier: str | None = None
    identifier_type: str | None = None
    validation_info: str | bool | None = True


def doi_from_pdf(file: FilePath, preprint: str) -> DOIFromPDFResult | None:
    metadata: dict = extract_metadata(file)
    title: str = metadata.get("Title", file.stem)
    handlers: dict = {
        find_identifier_in_metadata: (metadata,),
        find_identifier_in_pdf_info: (metadata,),
        find_identifier_in_text: (title, IDENTIFIER_PATTERNS, True),
        find_identifier_in_text: (preprint, IDENTIFIER_PATTERNS),
        find_identifier_by_googling_first_N_characters_in_pdf: (preprint,),
    }
    return next(filter(None, (handler(*args) for handler, args in handlers.items())), None)


def find_identifier_in_metadata(metadata: dict) -> DOIFromPDFResult | None:
    """
    Searches for a valid identifier (e.g., DOI, arXiv ID) within the given metadata dictionary.
    Prioritizes certain keys for a more efficient search.

    Parameters
    ----------
    metadata : dict
        A dictionary containing metadata key-value pairs.

    Returns
    -------
    DOIFromPDFResult | None
        A data class containing the identifier and its type if a valid identifier is found; otherwise, None.
    """
    priority_keys = {"doi", "pdf2doi_identifier", "arxiv"}

    logger.info(f"Method #1: Looking for a valid identifier in the document metadata...")

    for key in priority_keys:
        if initial_result := metadata.get(key):
            logger.info(f"Identifier found using Method #1 {initial_result}")
            return DOIFromPDFResult(identifier=initial_result, identifier_type=key)

    logger.info("Could not find a valid identifier in the most likely metadata keys.")


def find_identifier_in_pdf_info(metadata: dict[str, str]) -> DOIFromPDFResult | None:
    """
    Try to find a valid DOI in the values of the 'document information' dictionary.

    Parameters
    ----------
    file : object file
    Returns
    -------
    result : dictionary with identifier and other info (see above)
    """
    values_to_search = (value for key, value in metadata.items() if key != "/wps-journaldoi")

    for value in values_to_search:
        result = find_identifier_in_text(value)
        if result and result.identifier:
            logger.info(f"A valid {result.identifier_type} was found in the document info labelled '{value}'.")
            return result
        else:
            logger.info(f"No valid identifier found in the metadata key: '{value}'.")

    logger.info("Could not find a valid identifier in any of the metadata keys.")


def extract_metadata(file: FilePath) -> dict:
    with pdfplumber.open(file) as pdf:
        metadata = pdf.metadata
        logger.debug(metadata)
        return metadata


def find_identifier_in_text(
    text: str,
    pattern_dict: dict[re.Pattern[str], str] = IDENTIFIER_PATTERNS,
    title_search: bool = False,
) -> DOIFromPDFResult | None:
    """
    Searches for a valid identifier (e.g., DOI or arXiv ID) within a text.

    Parameters
    ----------
    text : str
        Text to be analyzed.

    Returns
    -------
    identifier : string
        A valid identifier if any is found, or None if nothing was found.
    pattern_dict : dict
        Dictionary containing regex patterns as keys and identifier types as values.
    title_search : bool
        Flag indicating whether the text is a title.

    """
    search_type = "title" if title_search else "text"

    for pattern, id_type in pattern_dict.items():
        logger.info(f"Searching for a valid {id_type.upper()} in the document {search_type}...")
        matches = pattern.findall(text)
        if not matches:
            logger.info(f"No valid {id_type.upper()} found in the document {search_type}.")
            continue
        identifier = matches[0]
        logger.debug(f"Potential {id_type.upper()} found: {identifier}")

        validation = validate_identifier(identifier, id_type)
        identifier = standardize_doi(identifier) if id_type == "doi" else identifier

        return DOIFromPDFResult(identifier, id_type, validation)


def validate_identifier(identifier: str, id_type: str) -> str | None:
    """
    Validate an identifier by querying appropriate URLs based on the identifier type.

    Parameters
    ----------
    identifier : str
        The identifier to be validated.
    id_type : str
        Type of the identifier ('arxiv' or 'doi').

    Returns
    -------
    str | None
        A string representation of the validation result, or None if validation fails.
    """
    try:
        if id_type == "arxiv":
            url = f"http://export.arxiv.org/api/query?search_query=id:{identifier}"
            result: FeedParserDict = feedparse(url)
            return str(result["entries"][0]) if result["entries"][0] else None
        elif id_type == "doi":
            url = f"http://dx.doi.org/{identifier}"
            headers = {"accept": "application/citeproc+json"}
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error("Some error occured within the function validate_doi_web: %s" % e)
        return None


def find_identifier_by_googling_first_N_characters_in_pdf(
    text: str,
    num_results: int = 3,
    num_characters: int = 50,
) -> DOIFromPDFResult | None:
    """
    Perform a Google search using the first N characters of the text and
    find an identifier in the search results.

    Parameters
    ----------
    text : str
    num_results : int
    num_characters : int
    websearch : bool
    """
    logger.info(
        f"Method #4: Trying to do a google search with the first {num_characters} characters of this pdf file..."
    )

    if not text.strip():
        logger.error("No meaningful text could be extracted from this file.")
        return None

    trimmed_text = text[:num_characters].lower()

    logger.info(f"Performing google search with first {num_results} characters of the text...")
    return find_identifier_in_google_search(trimmed_text, num_results)


def find_identifier_in_google_search(
    query: str, num_results: int = 3, max_length_display: int = 100
) -> DOIFromPDFResult | None:
    """Perform a Google search using the query and find an identifier in the search results.

    Parameters
    ----------
    query : str
        The search query.
    num_results : int
        The number of search results to consider.

    Returns
    -------
    DOIFromPDFResult | None
        The result object containing the identifier information, if found; otherwise, None.
    """
    query_to_display: str = query[0:max_length_display] if len(query) > max_length_display else query
    logger.info(f"Performing google search with key {query_to_display}, considering first {num_results} results...")
    for url in search(query, stop=num_results):
        result = find_identifier_in_text(url)

        if result and result.identifier:
            logger.info(f"A valid {result.identifier_type} was found in the search URL.")
            return result

    logger.info("No valid identifier found in the search results.")
    return None
