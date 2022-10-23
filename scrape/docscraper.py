import itertools
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Generator

import pdfplumber

UTF = "utf-8"
logger = logging.getLogger("sciscraper")

TextractStrategyFunction = Callable[[str],Generator[list[str],None,None]]

@dataclass(frozen=True, order=True)
class FreqDistAndCount:
    term_count: int
    frequency_dist: list[tuple[str, int]] = field(default_factory=list)

@dataclass(order=True)
class Wordscore:
    pos_part: float
    neg_part: float
    pos_chances: int
    neg_chances: int
    total_len: int
    formatted_worscore: str = ""

    def calc_wordscore(self): #odds ratio
        pos_odds = self.pos_part / self.pos_chances
        neg_odds = self.neg_part / self.neg_chances
        length_factor = 1 - (((self.pos_chances + self.neg_chances)/self.total_len) * 0.75)
        try:
            raw_wordscore = pos_odds / (pos_odds + neg_odds)
            raw_wordscore = raw_wordscore * length_factor
        except ZeroDivisionError as zero_error:
            logger.debug(zero_error)
            raw_wordscore = 0
        self.formatted_worscore = f"{raw_wordscore:.2%}"

@dataclass(frozen=True, order=True)
class DocumentResult:
    formatted_worscore: str
    target_freq: list = field(default_factory=list)
    bycatch_freq: list = field(default_factory=list)


def match_terms(target: list[str], word_set:set[str]) -> FreqDistAndCount:
    matching_set = (word for word in target if word in word_set)
    words = Counter(matching_set)
    matching_terms = words.most_common(3)
    term_count = sum(term[1] for term in matching_terms)
    return FreqDistAndCount(term_count,matching_terms)

@dataclass
class DocScraper:
    bycatch_words:str
    target_words:str
    is_pdf: bool = True

    def unpack_txt_files(self, txtfile: str) -> set[str]:
        """unpacks_txt_files takes a txt_file containing indended words.
        Args:
            txtfiles (str): filepath to the .txt file containing the words to analyze the document.
            stemmed (bool): determines whether or not to stem the words,
            so as to match all variations of them: plurals, adverbs, &c.
            Defaults to False.

        Returns:
            set[str]: a set of words against which the text will be compared.
        """
        with open(txtfile, encoding=UTF) as iowrapper:
            textlines = iowrapper.readlines()
            unstemmed = (word.strip().lower() for word in textlines)
            return {*unstemmed}
    
    def scrape(self, search_text: str) -> DocumentResult | None:
        tokgen = self.extract_text_from_pdf(search_text) if self.is_pdf else self.simple_text_clean(search_text)
        bycatch_size: int = len(self.bycatch_words)
        target_size: int = len(self.target_words)
        for tokens in tokgen:
            logger.info(tokens)
            total_len = len(tokens)
            target_set, bycatch_set = self.unpack_txt_files(self.target_words), self.unpack_txt_files(self.bycatch_words)
            target, bycatch = match_terms(tokens, target_set), match_terms(tokens, bycatch_set)
            pos_count, target_freq = target.term_count, target.frequency_dist
            neg_count, bycatch_freq = bycatch.term_count, bycatch.frequency_dist
            wordscore = Wordscore(pos_count, neg_count, bycatch_size, target_size, total_len)
            wordscore.calc_wordscore()

            return DocumentResult(
                wordscore.formatted_worscore,
                target_freq,
                bycatch_freq
            )

    def extract_text_from_pdf(self, search_text: str) -> Generator[list[str],None,None]:
        with pdfplumber.open(search_text) as study:
            study_pages = study.pages
            study_length = len(study_pages)
            pages_to_check = [*study_pages][:study_length]
            preprints = (study_pages[page_number].extract_text(x_tolerance=1,y_tolerance=3) for page_number, _ in enumerate(pages_to_check))
            manuscripts = (preprint.strip().lower() for preprint in preprints)
            manuscripts = (re.sub(r"\W+", " ", manuscript) for manuscript in manuscripts)
            draft = (manuscript.split(" ") for manuscript in manuscripts)
            yield list(itertools.chain.from_iterable((draft)))

    def simple_text_clean(self, search_text: str) -> Generator[list[str],None,None]:
        logger.info(search_text)
        manuscripts = search_text.strip().lower()
        logger.info(manuscripts)
        draft = (manuscripts.split(" "))
        logger.info(draft)
        yield draft
