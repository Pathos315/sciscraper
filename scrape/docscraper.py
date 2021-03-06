import logging
import re
from os import path
from typing import Any

import pdfplumber
from nltk import FreqDist
from nltk.corpus import names, stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
from textblob import TextBlob

from scrape.scraper import WordscoreResult

logger = logging.getLogger("sciscraper")

STOP_WORDS: set[str] = {*stopwords.words("english")}

NAME_WORDS: set[str] = {*names.words()}

stemmer = SnowballStemmer("english", ignore_stopwords=True)


def unpack_txt_files(txtfile: str, stemmed: bool = False) -> set[str]:
    """unpacks_txt_files takes a txt_file containing indended words.

    Args:
        txtfile (str): filepath to the .txt file containing the words to analyze the document.
        stemmed (bool): determines whether or not to stem the words,
        so as to match all variations of them: plurals, adverbs, &c.
        Defaults to False.

    Returns:
        set[str]: a set of words against which the text will be compared.
    """
    with open(txtfile, encoding="utf8") as iowrapper:
        textlines = iowrapper.readlines()
        unstemmed = [word.strip().lower() for word in textlines]
        if stemmed:
            return {stemmer.stem(word) for word in unstemmed}
        return {*unstemmed}


def overlap_word_sets(
    word_categories: dict[str, set[str]], all_words: list[str]
) -> dict[str, set[str]]:
    return {
        key: value.intersection(all_words) for key, value in word_categories.items()
    }


def frequency_from_dicts(
    overlapping_dict: dict[str, set[str]]
) -> dict[str, list[tuple[str, int]]]:
    return {key: most_common_words(value) for key, value in overlapping_dict.items()}


def guess_doi(path_name: str) -> str:
    """Guesses the digital identifier for the paper based on the filename"""
    basename: str = path.basename(path_name)
    doi = basename[7:-4]
    return f"{doi[:7]}/{doi[7:]}"


def compute_filtered_tokens(text: list[str] | Any) -> list[str]:
    """Takes a lowercase string, now removed of its non-alphanumeric characters.
    It returns (as a list comprehension) a parsed and tokenized
    version of the text, with stopwords and names removed.
    """
    word_tokens: list[str] = word_tokenize("\n".join(text))
    return [word for word in word_tokens if word not in STOP_WORDS & NAME_WORDS]


def most_common_words(word_set, amount: int = 4) -> list[tuple[Any, int]]:
    """most_common_words _summary_

    Args:
        word_set (set[str]): _description_
        n (int): _description_

    Returns:
        list[tuple[str, int]]: _description_
    """
    return FreqDist(word_set).most_common(amount)


class DocScraper:
    """DocScraper _summary_

    Args:
        Scraper (_type_): _description_
    """

    def __init__(
        self,
        target_words_path: str,
        bycatch_words_path: str,
        research_words_path: str,
        tech_words_path: str,
        impact_words_path: str,
        is_pdf: bool = True,
    ):
        self.target_words = unpack_txt_files(target_words_path)
        self.bycatch_words = unpack_txt_files(bycatch_words_path)
        self.research_words = unpack_txt_files(research_words_path)
        self.tech_words = unpack_txt_files(tech_words_path)
        self.impact_words = unpack_txt_files(impact_words_path)
        self.is_pdf = is_pdf

    def calc_wordscore(self, overlapping_dict: dict[str, set[str]]) -> int:
        wordscore = (
            len(overlapping_dict["target_words"])
            + len(overlapping_dict["impact_words"])
            + len(overlapping_dict["tech_words"])
        ) - (len(overlapping_dict["bycatch_words"]) * 3)
        return wordscore

    def all_words_from_abstract(self, search_text: str) -> list[str]:
        blob = TextBlob(search_text.lower())
        word_tokens = blob.words
        return compute_filtered_tokens(word_tokens)

    def all_words_from_pdf(self, search_text: str) -> list[str]:
        preprints: list[str] = []
        with pdfplumber.open(search_text) as study:
            pages: list[Any] = study.pages
            study_length = len(pages)
            pages_to_check = [*pages][:study_length]
            for page_number, page in enumerate(pages_to_check):
                page: str = pages[page_number].extract_text(
                    x_tolerance=3, y_tolerance=3
                )
                logger.info(
                    f"[sciscraper]: Processing Page {page_number} "
                    f"of {study_length-1} | {search_text}...",
                )
                preprints.append(
                    page
                )  # Each page's string gets appended to preprint []

            manuscripts = [preprint.strip().lower() for preprint in preprints]
            # The preprints are stripped of extraneous
            # characters and all made lower case.
            postprints = [re.sub(r"\W+", " ", manuscript) for manuscript in manuscripts]
            # The ensuing manuscripts are stripped of
            # lingering whitespace and non-alphanumeric characters.
            return compute_filtered_tokens(postprints)

    def scrape(self, search_text: str) -> WordscoreResult:
        """analyze _summary_

        Args:
            search_text (str): _description_

        Returns:
            AnalysisResult: _description_
        """
        word_categories: dict[str, set[str]] = {
            "target_words": self.target_words,
            "bycatch_words": self.bycatch_words,
            "research_words": self.research_words,
            "tech_words": self.tech_words,
            "impact_words": self.impact_words,
        }

        if self.is_pdf:
            all_words = self.all_words_from_pdf(search_text)
        else:
            all_words = self.all_words_from_abstract(search_text)

        # doi = guess_doi(search_text)
        overlap_dict = overlap_word_sets(word_categories, all_words)
        wordscore = self.calc_wordscore(overlap_dict)
        frequencies = frequency_from_dicts(overlap_dict)
        freq_from_all_words = most_common_words(all_words)

        return WordscoreResult(
            wordscore=wordscore,
            most_freq_target_words=frequencies["target_words"],
            most_freq_all_words=freq_from_all_words,
            study_design_hunch=frequencies["research_words"],
            impact_of_study_hunch=frequencies["impact_words"],
            tech_words_freq=frequencies["tech_words"],
        )
