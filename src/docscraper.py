from __future__ import annotations

import re

from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any

import pdfplumber

from src.config import UTF
from src.doifrompdf import doi_from_pdf
from src.log import logger


if TYPE_CHECKING:
    from pathlib import Path

    from pydantic import FilePath


PAPER_STATISTIC = re.compile(r"\(.*\=.*\)")


@dataclass(frozen=True)
class FreqDistAndCount:
    """FreqDistAndCount

    A dataclass with a the 3 most common words
    that were found in both the target and the set,
    and the sum of the frequencies of those matching words.

    Attributes:
        term_count(int): A cumulative count of the frequencies
            of the three most common words within the text.
        frequency_dist(list[tuple[str,int]]): A list of three tuples,
            each tuple containing the word and its frequency within the text.
    """

    term_count: int
    frequency_dist: list[tuple[str, int]] = field(default_factory=list)


@dataclass(frozen=True)
class DocumentResult:
    """DocumentResult contains the WordscoreCalculator\
    scoring relevance, and two lists, each with\
    the three most frequent target and bycatch words respectively.\
    This gets passed back to a pandas dataframe.\
    """

    doi_from_pdf: str | None
    matching_terms: int
    bycatch_terms: int
    total_word_count: int
    wordscore: float
    target_terms_top_3: list[tuple[str, int]] = field(default_factory=list)
    bycatch_terms_top_3: list[tuple[str, int]] = field(default_factory=list)
    paper_parentheticals: list[Any] = field(default_factory=list)


def match_terms(target: list[str], word_set: set[str]) -> FreqDistAndCount:
    """
    Calculates the relevance of the paper, or abstract, as a percentage.

    Parameters:
        target(list[str]): The list of words to be assessed.
        wordset(set[str]): The set of words against which the target words will be compared.

    Returns:
        FreqDistAndCount: A dataclass with a the 3 most common words that were found in
        both the target and the set, and the sum of the frequencies of those matching words.

    Example
    --------
    ```
    # Note in the following example
    # that more frequent 'd'
    # from word_list will be absent

    >>> word_list                   = ['a','a','b','c','d',
                                   'd','d','d','c','a',
                                   'f','f','f','g','d']
    >>> word_set                    = {'a','b','f'}
    >>> output: FreqDistAndCount    = match_terms(word_list,word_set)
    >>> output.matching_terms       = [('a',3),('f',3),('b',1)]
    >>> output.term_count           = 7
    """

    matching_terms = Counter(
        word for word in target if word in word_set
    ).most_common(3)
    term_count = sum(term[1] for term in matching_terms)
    freq = FreqDistAndCount(term_count, matching_terms)
    logger.debug(
        "match_terms=%r,\
        frequent_terms=%s",
        match_terms,
        freq,
    )
    return freq


@dataclass
class DocScraper:
    """
    DocScraper takes two .txt files and either a full .pdf or an abstract.
    From these, it generates an analysis of its relevance,
    according to provided target and bycatch words, in the form of
    a percentage grade called WordscoreCalculator.
    """

    target_words_file: Path
    bycatch_words_file: Path
    is_pdf: bool = True

    def unpack_txt_files(self, txtfile: FilePath) -> set[str]:
        """
        Opens a .txt file containing the words that will analyze
        the ensuing passage, and creates a set with those words.

        Parameters:
            txtfiles(FilePath): The filepath to the .txt file containing the words that
            will analyze the document.

        Returns:
            set[str]: A set of words against which the text will be compared.
        """
        with open(txtfile, encoding=UTF) as iowrapper:
            wordset = {word.strip().lower() for word in iowrapper}
            logger.debug(
                "func=%s, word_set=%s", self.unpack_txt_files, wordset
            )
            return wordset

    def obtain(self, search_text: str) -> DocumentResult | None:
        """
        Given the provided search string, it extracts the text from
        the pdf or abstract provided, it cleans the text in question,
        and then it compares the cleaned data against the provided
        sets of words to assess relevance.

        Parameters:
            search_text(str) : The initially provided search string from
                a prior list comprehension, often in the form of either a filepath or the abstract of a paper.

        Returns:
            DocumentResult | None : It either returns a formatted DocumentResult dataclass, which is
            sent back to a dataframe, or it returns None.
        """

        logger.debug(repr(self))
        target_set = self.unpack_txt_files(self.target_words_file)
        bycatch_set = self.unpack_txt_files(self.bycatch_words_file)
        preprint: str = (
            self.extract_text_from_pdf(search_text)
            if self.is_pdf
            else search_text
        )
        digital_object_identifier = doi_from_pdf(search_text, preprint).identifier if self.is_pdf else None  # type: ignore
        token_list: list[str] = self.format_manuscript(preprint)
        target = match_terms(token_list, target_set)
        bycatch = match_terms(token_list, bycatch_set)
        total_word_count = len(token_list)
        wordscore: float = target.term_count / 1 + bycatch.term_count
        doc = DocumentResult(
            doi_from_pdf=digital_object_identifier,
            matching_terms=target.term_count,
            bycatch_terms=bycatch.term_count,
            total_word_count=total_word_count,
            wordscore=wordscore,
            target_terms_top_3=target.frequency_dist,
            bycatch_terms_top_3=bycatch.frequency_dist,
            paper_parentheticals=PAPER_STATISTIC.findall(preprint),
        )
        logger.debug(repr(doc))
        return doc

    def format_manuscript(self, preprint: str) -> list[str]:
        return preprint.strip().lower().split(" ")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Given the provided filepath, `search_text`, it opens the .pdf
        file and cleans the text. Returning the words from each page
        as a Generator object.

        Parameters:
            search_text(str): The initially provided filepath from a prior list comprehension.

        Returns:
            str: A string of unformatted words from the entire document.
        """
        with pdfplumber.open(pdf_path) as pdf:
            text_pages = [
                page.extract_text(x_tolerance=1, y_tolerance=3)
                for page in pdf.pages
            ]
        return " ".join(text_pages)
