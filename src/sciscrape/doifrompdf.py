from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from typing import Any

import pdfplumber
import requests
from feedparser import FeedParserDict
from feedparser import parse as feedparse
from googlesearch import search

from sciscrape.doi_regex import ARXIV_VERSIONS, DOI_VERSIONS, standardize_doi
from sciscrape.log import logger
from sciscrape.webscrapers import client

KEYS_TO_AVOID = ['/wps-journaldoi']

@dataclass(frozen=True)
class DOIFromPDFResult:
    identifier: str | None = None
    identifier_type: str | None = None
    validation_info: str | bool | None = True


def doi_from_pdf(file: pathlib.Path, preprint: str) -> DOIFromPDFResult:
    metadata: dict = extract_metadata(file)
    title: str = metadata.get('Title', file.stem)
    handlers: dict = {
        find_identifier_in_metadata: (metadata,),
        find_identifier_in_pdf_info: (metadata,),
        find_identifier_in_text: (title, DOI_VERSIONS, "doi", True),
        find_identifier_in_text: (preprint, DOI_VERSIONS, "doi"),
        find_identifier_in_text: (title, ARXIV_VERSIONS, "arxiv", True),
        find_identifier_in_text: (preprint, ARXIV_VERSIONS, "arxiv"),
        find_identifier_by_googling_first_N_characters_in_pdf: (preprint,),
    }
    return next(filter(None, (handler(*args) for handler, args in handlers.items())), None)


def find_identifier_in_metadata(metadata: dict) -> DOIFromPDFResult:
    logger.info(f"Method #1: Looking for a valid identifier in the document metadata...")
    for key in ['doi','pdf2doi_identifier','arxiv']:
        if (initial_result := metadata.get(key)):
            logger.info(f"Identifier found using Method #1 {initial_result}")
            return DOIFromPDFResult(identifier=initial_result, identifier_type=key)


def find_identifier_in_pdf_info(metadata: dict[str, str]) -> DOIFromPDFResult:
    """
    Try to find a valid DOI in the values of the 'document information' dictionary. If a list of string is specified via the optional
    input parameter 'keys_to_check_first', then the corresponding elements of the dictionary (assuming that the key exists) are given
    priority.

    Parameters
    ----------
    file : object file
    Returns
    -------
    result : dictionary with identifier and other info (see above)
    """
    values = (value for key, value in metadata.items() if key not in KEYS_TO_AVOID)
    for value in values:
        result = find_identifier_in_text(value, DOI_VERSIONS, "doi")
        if not result.identifier:
            result = find_identifier_in_text(value, ARXIV_VERSIONS, "arxiv")
        if result.identifier:
            logger.info(f"A valid {result.identifier_type} was found in the document info labelled \'{value}\'.")
            break
        else:
            logger.info("Could not find a valid identifier in the document info.")
    return result


def extract_metadata(file: pathlib.Path) -> dict:
    with pdfplumber.open(file) as pdf:
        metadata = pdf.metadata
        logger.debug(metadata)
    return metadata


def find_identifier_in_text(text: str, pattern_list: list[re.Pattern[str]], id_type: str, title_search: bool = False) -> DOIFromPDFResult:
    """
    Given any string (or list of strings), it looks for any pattern which matches a valid identifier (e.g. a DOi or an arXiv ID).
    If a list of string is passed as an argument, they are checked in the order in which they appear in the list,
    and the function stops as soon as a valid identifier is found.

    Parameters
    ----------
    texts : string or a list of strings
       text to analyse.

    Returns
    -------
    identifier : string
        A valid identifier if any is found, or None if nothing was found.
    desc : string
        Description of what was found (e.g. 'doi,''arxiv')
    validation : string or True
        The result returned by the function func_validate. If web validation is enabled, this is typically a bibtex entry for this
        publication. Otherwise, it is just equal to True

    """
    title_search_var: str = "title" if title_search else "text"
    logger.info(f"Method #2-{id_type} in {title_search_var}: Looking for a valid {id_type.upper()} in the document {title_search_var}...")
    identifiers = (pattern.findall(text) for pattern in pattern_list)
    for identifier in identifiers:
        logger.debug(f"Found a potential {id_type}: {identifier}")
        validation = validate_identifier(identifier, id_type)
        identifier = standardize_doi(identifier) if id_type == 'doi' else identifier
    return DOIFromPDFResult(identifier, id_type, validation,)


def validate_identifier(identifier: str, id_type: str) -> str | None:
    if id_type == 'arxiv':
        url = f"http://export.arxiv.org/api/query?search_query=id:{identifier}"
        result: FeedParserDict = feedparse(url)
        return str(result['entries'][0]) or None
    url = f"http://dx.doi.org/{identifier}"
    headers = {"accept": 'application/citeproc+json'}
    try:
        text = client.get(url, headers = headers).text
    except Exception as e:
        logger.error("Some error occured within the function validate_doi_web: %s" % e)
    return text or None


def find_identifier_by_googling_first_N_characters_in_pdf(text: str, num_results: int = 3, num_characters: int = 50, websearch:bool = True,) -> DOIFromPDFResult:
    """
    Parameters
    ----------
    file : object file
    func_validate : function, optional
    num_results : int
    num_characters : int
    """
    logger.info(
        f"Method #4: Trying to do a google search with the first {num_characters} characters of this pdf file...")

    if not websearch:
        logger.info("NOTE: Web-search methods are currently disabled by the user. Enable it in order to use this method.")

    text: str = text.lower()
    if text=="":
        logger.error("No meaningful text could be extracted from this file.")

    logger.info(f"Doing a google search, looking at the first {num_results} results...")
    result = find_identifier_in_google_search(text, num_results)
    if result.identifier:
        logger.info(f"A valid {result.identifier_type} was found with this google search.")
    logger.info(f"Could not find a valid identifier by googling the first {num_characters} characters extracted from the pdf file.")
    return result


def find_identifier_in_google_search(query: str, num_results: int = 3) -> DOIFromPDFResult:
    max_length_display = 100
    query_to_display = query[0:max_length_display] if len(query)>max_length_display else query
    logger.info(f"Performing google search with key {query_to_display} and looking at the first {num_results} results...")
    counter = 1
    result = DOIFromPDFResult()
    try:
        for url in search(query, stop=num_results):
            result: DOIFromPDFResult = find_identifier_in_text([url])
            if result.identifier:
                logger.info(f"A valid {result.identifier_type} was found in the search URL.")
                return result
            logger.info(f"Looking for a valid identifier in the search result #{counter} : {url}")
            response_text = requests.get(url).text
            result = find_identifier_in_text(response_text)
            if result.identifier:
                return result
            counter += 1
    except Exception as e:
        logger.error('Some error occured while doing a google search (maybe the string is too long?) %s' % e)
    return result

