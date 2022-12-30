from dotenv import load_dotenv
from os import getenv

from itertools import chain
from json import loads
import pdfplumber
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Generator, Optional
from sciscrape.wordscore import RelevanceCalculator
from sciscrape.webscrapers import WebScraper, client
from sciscrape.log import logger
from sciscrape.config import UTF, FilePath, config


load_dotenv()
API_KEY = getenv("api_key")


@dataclass(slots=True, frozen=True, order=True)
class FreqDistAndCount:
    """FreqDistAndCount

    A dataclass with a the 3 most common words
    that were found in both the target and the set,
    and the sum of the frequencies of those matching words.

    Attributes
    ----------
    term_count : int
        A cumulative count of the frequencies of
        the three most common words within the text.
    frequency_dist : list[tuple[str,int]]
        A list of three tuples, each tuple containing
        the word and its frequency within the text.
    """

    term_count: int
    frequency_dist: list[tuple[str, int]] = field(default_factory=list)


@dataclass(slots=True, frozen=True, order=True)
class DocumentResult:
    """DocumentResult contains the RelevanceCalculator\
    scoring relevance, and two lists, each with\
    the three most frequent target and bycatch words respectively.\
    This gets passed back to a pandas dataframe.\
    """

    summary: str
    relevance_scores: list[tuple[str, float]]
    wordscore: float
    target_freq: list[tuple[str, int]] = field(default_factory=list)
    bycatch_freq: list[tuple[str, int]] = field(default_factory=list)


def match_terms(target: list[str], word_set: set[str]) -> FreqDistAndCount:
    """
    Calculates the relevance of the paper, or abstract, as a percentage.

    Parameters
    ----------
    target : list[str]
        The list of words to be assessed.
    wordset : set[str]
        The set of words against which the target words will be compared.

    Returns
    -------
    FreqDistAndCount
        A dataclass with a the 3 most common words that were found in
        both the target and the set, and the sum of the frequencies
        of those matching words.

    Example
    --------
    ```
    # Note in the following example
    # that more frequent 'd'
    # from word_list will be absent

    word_list                   = ['a','a','b','c','d',
                                   'd','d','d','c','a',
                                   'f','f','f','g','d']
    word_set                    = {'a','b','f'}
    output: FreqDistAndCount    = match_terms(word_list,word_set)
    output.matching_terms       = [('a',3),('f',3),('b',1)]
    output.term_count           = 7
    """

    matching_terms: list[tuple[str, int]] = Counter(
        (word for word in target if word in word_set)
    ).most_common(3)
    term_count: int = sum(term[1] for term in matching_terms)
    freq: FreqDistAndCount = FreqDistAndCount(term_count, matching_terms)
    logger.debug(
        "match_terms=%s,\
        frequent_terms=%s",
        repr(match_terms),
        freq,
    )
    return freq


@dataclass(slots=True)
class DocScraper:
    """
    DocScraper takes two .txt files and either a full .pdf or an abstract.
    From these, it generates an analysis of its relevance,
    according to provided target and bycatch words, in the form of
    a percentage grade called RelevanceCalculator.
    """

    target_words_file: str
    bycatch_words_file: str
    is_pdf: bool = True

    def unpack_txt_files(self, txtfile: FilePath) -> set[str]:
        """
        Opens a .txt file containing the words that will analyze
        the ensuing passage, and creates a set with those words.

        Parameters
        ----------
        txtfiles : str
            The filepath to the .txt file containing the words that
            will analyze the document.

        Returns
        -------
        set[str]
            A set of words against which the text will be compared.
        """
        with open(txtfile, encoding=UTF) as iowrapper:
            textlines: list[str] = iowrapper.readlines()
            wordset: set[str] = {word.strip().lower() for word in textlines}
            logger.debug("func=%s, word_set=%s", repr(self.unpack_txt_files), wordset)
            return wordset

    def obtain(self, search_text: str) -> Optional[DocumentResult]:
        """
        Given the provided search string, it extracts the text from
        the pdf or abstract provided, it cleans the text in question,
        and then it compares the cleaned data against the provided
        sets of words to assess relevance.

        Parameters
        ----------
        search_text : str
            The initially provided search string from a prior list
            comprehension, often in the form of a filepath
            or the abstract of a paper.

        Returns
        -------
        DocumentResult | None
            It either returns a formatted DocumentResult dataclass, which is
            sent back to a dataframe, or
            it returns None.
        """

        logger.debug(repr(self))

        target_set = self.unpack_txt_files(self.target_words_file)
        bycatch_set = self.unpack_txt_files(self.bycatch_words_file)

        token_generator: Generator[list[str], None, None] = (
            self.extract_text_from_pdf(search_text)
            if self.is_pdf
            else self.extract_text_from_summary(search_text)
        )

        token_list = next(token_generator)
        summary = TLDRScraper(
            url=config.sci_tldr_url,
            sleep_val=0.2,
        ).obtain(search_text)
        relevance_scores, implicature_score = ZeroShotClassifier(
            url=config.zero_classifier_url,
            sleep_val=0.2,
        ).obtain(search_text)
        target: FreqDistAndCount = match_terms(token_list, target_set)
        bycatch: FreqDistAndCount = match_terms(token_list, bycatch_set)
        wordcalc = RelevanceCalculator(
            target.term_count,
            bycatch.term_count,
            len(token_list),
            implicature_score,
        )
        logger.debug(repr(wordcalc))

        doc = DocumentResult(
            summary,
            relevance_scores,
            wordcalc(),
            target.frequency_dist,
            bycatch.frequency_dist,
        )
        logger.debug(repr(doc))
        return doc

    def extract_text_from_pdf(
        self, search_text: str
    ) -> Generator[list[str], None, None]:
        """
        Given the provided filepath, `search_text`, it opens the .pdf
        file and cleans the text. Returning the words from each page
        as a Generator object.

        Parameters
        ----------
        search_text : str
            The initially provided filepath from a prior list comprehension.

        Yields
        -------
        Generator
            A generator with cleaned words from each entire document.

        See Also
        -------
        extract_text_from_summary : Extract text from academic paper abstracts.
        """
        with pdfplumber.open(search_text) as study:
            study_pages: list[Any] = study.pages
            study_length: int = len(study_pages)
            pages_to_check: list[Any] = [*study_pages][:study_length]
            logger.debug(
                "func=%s,\
                study_length=%s,\
                query=%s",
                repr(self.extract_text_from_pdf),
                pages_to_check,
                search_text,
            )
            # Goes through all pages and creates a continuous string of text from the entire document
            preprints: Generator[str, None, None] = (
                study_pages[page_number].extract_text(x_tolerance=1, y_tolerance=3)
                for page_number, _ in enumerate(pages_to_check)
            )

            # Strips and lowers every word
            manuscripts: Generator[Any, None, None] = (
                preprint.strip().lower() for preprint in preprints
            )

            # Regularizes white spaces
            manuscripts = (
                re.sub(r"\W+", " ", manuscript) for manuscript in manuscripts
            )

            # Splits each word along each white space to create a list of strings from each word
            output: Generator[list[str], None, None] = (
                manuscript.split(" ") for manuscript in manuscripts
            )
            logger.debug(
                "func=%s,\
                output=%s",
                repr(self.extract_text_from_pdf),
                output,
            )

            yield list(chain.from_iterable((output)))

    def extract_text_from_summary(
        self, search_text: str
    ) -> Generator[list[str], None, None]:
        """
        Given the provided abstract, `search_text`, it reads the text
        and cleans it. Returning the words from each
        abstract as a generator object.

        Parameters
        ----------
        search_text : str
            The initially provided abstract from a prior list comprehension.

        Yields
        -------
        Generator
            A generator with cleaned words from each paper's abstract.

        See Also
        -------
        extract_text_from_pdf : Extract text from PDF files.
        """
        logger.debug(
            "func=%s,\
            query=%s",
            repr(self.extract_text_from_summary),
            search_text,
        )
        manuscript: str = search_text.strip().lower()
        output: list[str] = manuscript.split(" ")
        logger.debug(
            "func=%s,\
            output=%s",
            repr(self.extract_text_from_summary),
            repr(output),
        )
        yield output


@dataclass(slots=True)
class TLDRScraper(WebScraper):
    """
    OverviewScraper is a webscraper for
    summarizing paper abstracts.
    """

    def obtain(self, search_text: str) -> str:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = client.post(self.url, headers=headers, json=search_text)
        logger.debug(
            "search_text=%s, scraper=%s, status_code=%s",
            search_text,
            repr(self),
            response.status_code,
        )
        docs = loads(response.text)
        return self.navigate_api(docs)

    def navigate_api(self, docs: Any) -> str:
        try:
            item = docs[0]
            tldr: str = item.get("generated_text")
        except KeyError:
            tldr = "N/A"
        return tldr


@dataclass(slots=True)
class ZeroShotClassifier(WebScraper):
    """_summary_

    Parameters
    ----------
    WebScraper : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """

    def obtain(self, search_text: str) -> tuple[list[tuple[str, float]], float]:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        querystring = self.create_querystring(search_text)
        response = client.post(self.url, headers=headers, json=querystring)
        logger.debug(
            "search_text=%s, scraper=%s, status_code=%s",
            search_text,
            repr(self),
            response.status_code,
        )
        raw_relevance: dict[str, Any] = loads(response.text)
        relevance_score, implicature_score = self.zip_raw_relevance_values(
            raw_relevance
        )
        return relevance_score, implicature_score

    def create_querystring(
        self,
        search_text: str,
        candidate_labels: list[str] = [
            "prosocial behaviors",
            "social media",
            "design interventions",
            "user experience design",
            "cyberbullying",
        ],
    ) -> dict[str, Any]:
        return {
            "inputs": search_text,
            "parameters": {"candidate_labels": candidate_labels},
        }

    def zip_raw_relevance_values(
        self, raw_relevance: dict
    ) -> tuple[list[tuple[str, float]], float]:
        labels: list[str] = raw_relevance["labels"]
        labels = [str.title(label) for label in labels]
        scores: list[float] = raw_relevance["scores"]
        implicature_score = scores[0]
        relevance_scores = list(zip(labels, scores))

        logger.debug(f"\n{labels}\n{scores}\n=>{relevance_scores}")
        return relevance_scores, implicature_score
