r"""Contains methods that take various files, which each
return varying dataframes or directories for each"""

from collections import Counter
from enum import Enum
from fnmatch import fnmatch
from os import listdir, path

import pandas as pd
from tqdm import tqdm

from scrape.config import ScrapeConfig
from scrape.jsonscraper import JSONScraper
from scrape.log import logger
from scrape.docscraper import DocScraper


class Column(Enum):
    DOI = "doi"
    TITLE = "title"
    ABSTRACT = "abstract"
    ID = "id"
    CITED = "cited_dimensions_ids"
    WORDSCORE = "wordscore"

def filter_types(data) -> list[str]:
    """filter_types _summary_

    Args:
        data (_type_): _description_

    Returns:
        list[str]: _description_
    """
    return [
        search_text
        for search_text in target
        if not isinstance(search_text, (type(None), float))
    ]

def serialize_data(target: pd.DataFrame, column: Column, filtered: bool = True) -> list:
    series: pd.Series = target[column]
    series_list = series.to_list()
    if not filtered:
        return series_list
    return filter_types(series_list)

def unpack_csv(target: str, column: Column, filtered: bool = True) -> list[str]:
    """unpack_csv reads a previously formatted .csv file of papers, identifies
        a specific column of interest, and returns a list of entries,
        with invalid fields either dropped or not.

    Args:
        target (str): the target .csv file as a pathname
        column (Column): the column as a string. Note: It MUST be "doi", "title", "cited_dimensions_ids", "abstract", or "id".
        filtered (bool, optional): Either drop the invalid fields or not. Defaults to True.

    Returns:
        list[str]: A list of entries from the provided column.
    """
    with open(target, newline="", encoding="utf-8") as file_wrapper:
        data_from_csv: pd.Series = pd.read_csv(
            file_wrapper, skip_blank_lines=True, usecols=[column]
        )[column]
        unfiltered_terms: list[str] = data_from_csv.drop_duplicates().to_list()
        if not filtered:
            return unfiltered_terms
        filtered_data: list[str] = filter_types(unfiltered_terms)
        return filtered_data

def filter_neg_wordscores(
    target: pd.DataFrame, col: Column = "wordscore"
) -> pd.DataFrame:
    filt = target[col] > int(1)
    return target.loc[filt]

def fetch_terms_from_csv(
    target: str, column: Column, config: ScrapeConfig
) -> pd.DataFrame:
    """fetch_terms_from_doi reads a csv file line by line,
    isolating digital object identifiers (DOIs),
    scrapes the web for each DOIs bibliographic data,
    and places all of that resulting data into a pandas dataframe.
    """
    search_terms: list[str] = unpack_csv(target, column)
    scraper = JSONScraper(config.citations_dataset_url, False)
    return pd.DataFrame(
        [
            scraper.download(search_text)
            for search_text in tqdm(
                search_terms,
                desc=f"Getting entries via their {column} from csv: {target}",
                unit=column,
            )
        ]
    )


def fetch_abstracts_from_dataframe(
    target: pd.DataFrame, config: ScrapeConfig
) -> pd.DataFrame:
    """get_abstracts _summary_

    Args:
        target (pd.DataFrame): _description_
    """
    subset_dict: dict = {"_doi": target["doi"], "_title": target["title"]}
    subset_dataframe: pd.DataFrame = pd.DataFrame(data=subset_dict)
    abstracts: list = serialize_data(target, "abstract")

    scraper = TextScraper(
        target_words_path=config.target_words,
        bycatch_words_path=config.bycatch_words,
        research_words_path=config.research_words,
        tech_words_path=config.tech_words,
        impact_words_path=config.solution_words,
        is_pdf=False,
    )

    return pd.DataFrame(
        [scraper.scrape(summary) for summary in tqdm(abstracts, unit="abstract")]
    ).join(subset_dataframe, how="left", lsuffix="_source")


def fetch_terms_from_pubid(target: pd.DataFrame, config: ScrapeConfig) -> pd.DataFrame:
    """fetch_terms_from_pubid reads a pandas DataFrame,
    takes the cited_dimensions_ids from the DimensionsAPI
    further scrapes the dimensions.ai API for each listed pub_id for each paper, and returns
    bibliographic information for each cited paper.

    Args:
        target (pd.DataFrame): A pandas dataframe.

    Returns:
        pd.DataFrame: a dataframe containing the
        bibliographic information for each of the provided citations
    """
    data_frame: pd.DataFrame = target.explode("cited_dimensions_ids", "title")
    search_terms: list = serialize_data(data_frame, "cited_dimensions_ids")
    scraper = JSONScraper(config.citations_dataset_url, False)
    src_title: pd.Series = data_frame["title"]

    return pd.DataFrame(
        [
            scraper.download(search_text)
            for search_text in tqdm(search_terms, unit="citation")
        ]
    ).join(src_title, how="left", lsuffix="_source")


def fetch_citations_hence(target: pd.DataFrame, config: ScrapeConfig) -> pd.DataFrame:
    """fetch_citations_hence reads a pandas DataFrame,
    takes the provided pubIDs
    scrapes the dimensions.ai API for papers that went on to site site the initially provided paper,
    and it returns bibliographic information on each paper that mentions the initially provided papers.

    Args:
        target (pd.DataFrame): A pandas dataframe.

    Returns:
        pd.DataFrame:  a dataframe containing the bibliographic information for each paper
        that went on to site the initially provided paper
    """
    search_terms = serialize_data(target, "id")
    scraper = JSONScraper(config.citations_dataset_url, True)
    return pd.DataFrame(
        [
            scraper.download(search_text)
            for search_text in tqdm(search_terms, unit="derived papers")
        ]
    )


def fetch_terms_from_pdf_files(config: ScrapeConfig) -> pd.DataFrame:
    """fetch_terms_from_pdf_files goes into a directory, reads through
    each pdf file, parses the text, and then generates entries in a dataframe

    Args:
        config (ScrapeConfig): the directory to be parsed

    Returns:
        pd.DataFrame: the dataframe containing bibliographic data on each pdf.
    """

    search_terms = [
        path.join(config.test_src, file)
        for file in listdir(config.test_src)
        if fnmatch(path.basename(file), "*.pdf")
    ]
    scraper = TextScraper(
        target_words_path=config.target_words,
        bycatch_words_path=config.bycatch_words,
        research_words_path=config.research_words,
        tech_words_path=config.tech_words,
        impact_words_path=config.solution_words,
    )
    return pd.DataFrame(
        [scraper.scrape(file) for file in tqdm(search_terms, unit="file")]
    )



def fetch_abstracts_from_csv(target: str, config: ScrapeConfig) -> pd.DataFrame:
    """get_abstracts _summary_

    Args:
        target (pd.DataFrame): _description_
    """
    abstracts: list[str] = unpack_csv(target, "abstract")

    scraper = TextScraper(
        target_words_path=config.target_words,
        bycatch_words_path=config.bycatch_words,
        research_words_path=config.research_words,
        tech_words_path=config.tech_words,
        impact_words_path=config.solution_words,
        is_pdf=False,
    )

    return pd.DataFrame(
        [scraper.scrape(summary) for summary in tqdm(abstracts, unit="abstract")]
    )
