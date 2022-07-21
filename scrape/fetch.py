r"""Contains methods that take various files, which each
return varying dataframes or directories for each"""

import logging
from fnmatch import fnmatch
from os import listdir, path

import pandas as pd
from tqdm import tqdm

from scrape.config import read_config
from scrape.docscraper import DocScraper
from scrape.jsonscraper import JSONScraper
from scrape.log import logger

config = read_config("./config.json")


def run(strategy: str, target: str | pd.DataFrame) -> pd.DataFrame:
    SCRAPE_STRATEGIES = {
        "doi": fetch_terms_from_doi,
        "references": fetch_references,
        "citations": fetch_citations,
        "pdfs": fetch_pdfs_from_directory,
        "csv_abstracts": fetch_abstracts_from_csv,
        "df_abstracts": fetch_abstracts_from_dataframe,
    }

    return SCRAPE_STRATEGIES[strategy](target)


def filter_types(target: list):
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


def unpack_csv(target: str, _colsinuse: str, filtered: bool = True) -> list[str]:
    """unpack_csv reads a previously formatted .csv file of papers, identifies
        a specific column of interest, and returns a list of entries,
        with invalid fields either dropped or not.

    Args:
        target (str): the target .csv file as a pathname
        filtered (bool, optional): Either drop the invalid fields or not. Defaults to True.

    Returns:
        list[str]: A list of entries from the provided column."""
    with open(target, newline="", encoding="utf-8") as file_wrapper:
        data_from_csv: pd.Series = pd.read_csv(
            file_wrapper, skip_blank_lines=True, usecols=[_colsinuse]  # type: ignore
        ).drop_duplicates()[_colsinuse]
        unfiltered_terms: list[str] = data_from_csv.to_list()
        if filtered:
            return filter_types(unfiltered_terms)
        return unfiltered_terms


def serialize_data(
    target: pd.DataFrame, column: str, remove_empty: bool = True
) -> list:
    series: pd.Series = target[column]  # type: ignore
    series_list = series.to_list()
    if remove_empty:
        return filter_types(series_list)
    return series_list


def logging_level(verbose):
    if verbose:
        return logger.setLevel(logging.DEBUG)


def fetch_terms_from_doi(target: str) -> pd.DataFrame:
    """fetch_terms_from_doi reads a csv file line by line,
    isolating digital object identifiers (DOIs),
    scrapes the web for each DOIs bibliographic data,
    and places all of that resulting data into a pandas dataframe.
    Args:
        target (str): A .csv file
    Returns:
        pd.DataFrame: a dataframe containing the bibliographic information of the provided papers
    """
    logger.info("Getting entries from file: %s" % target)
    data_frame = unpack_csv(target, "doi")
    search_terms = filter_types(data_frame)
    scraper = JSONScraper(config.citations_dataset_url, False)
    return pd.DataFrame(
        [scraper.scrape(search_text) for search_text in tqdm(search_terms)]
    )


def fetch_terms_from_titles(target: str) -> pd.DataFrame:
    data_frame = unpack_csv(target, "title")
    search_terms = filter_types(data_frame)
    scraper = JSONScraper(config.citations_dataset_url, False)
    return pd.DataFrame(
        [scraper.scrape(search_text) for search_text in tqdm(search_terms)]
    )


def fetch_references(target: pd.DataFrame) -> pd.DataFrame:
    """fetch_references reads a pandas DataFrame,
    takes the cited_dimensions_ids from the result of a prior fetch_terms_from_doi method
    scrapes the dimensions.ai API for each listed pub_id for each paper, and returns
    bibliographic information for each cited paper.
    Args:
        target (pd.DataFrame): A pandas dataframe.
    Returns:
        pd.DataFrame: a dataframe containing the
        bibliographic information for each of the provided citations
    """
    data_frame: pd.DataFrame = target.explode(("cited_dimensions_ids", "title"))
    scraper = JSONScraper(config.citations_dataset_url, False)
    search_terms: list[str] = filter_types(data_frame["cited_dimensions_ids"].tolist())
    src_title: pd.Series = data_frame["title"]

    return pd.DataFrame(
        [scraper.scrape(search_text) for search_text in tqdm(search_terms)]
    ).join(src_title)


def fetch_citations(target: pd.DataFrame) -> pd.DataFrame:
    """fetch_citations_hence reads a pandas DataFrame,
    takes the provided pubIDs
    scrapes the dimensions.ai API for papers that went on to site site the initially provided paper,
    and it returns bibliographic information on each cited paper.
    Args:
        target (pd.DataFrame): A pandas dataframe.
    Returns:
        pd.DataFrame:  a dataframe containing the bibliographic information for each paper
        that went on to site the initially provided paper
    """
    search_terms: list[str] = filter_types(target["id"].tolist())
    scraper = JSONScraper(config.citations_dataset_url, True)
    return pd.DataFrame(
        [scraper.scrape(search_text) for search_text in tqdm(search_terms)]
    )


def fetch_pdfs_from_directory(target: str) -> pd.DataFrame:
    """fetch_terms_from_pdf_files goes into a directory, reads through
    each pdf file, parses the text, and then generates entries in a dataframe
    Args:
        config (ScrapeConfig): the directory to be parsed
    Returns:
        pd.DataFrame: the dataframe containing bibliographic data on each article.
    """

    search_terms = [
        path.join(target, file)
        for file in listdir(target)
        if fnmatch(path.basename(file), "*.pdf")
    ]
    scraper = DocScraper(
        target_words_path=config.target_words,
        bycatch_words_path=config.bycatch_words,
        research_words_path=config.research_words,
        tech_words_path=config.tech_words,
        impact_words_path=config.solution_words,
    )
    return pd.DataFrame([scraper.scrape(file) for file in tqdm(search_terms)])


def fetch_abstracts_from_csv(target: str) -> pd.DataFrame:
    """get_abstracts _summary_
    Args:
        target (pd.DataFrame): _description_
    """
    abstracts: list[str] = unpack_csv(target, "abstract")

    summarizer = DocScraper(
        target_words_path=config.target_words,
        bycatch_words_path=config.bycatch_words,
        research_words_path=config.research_words,
        tech_words_path=config.tech_words,
        impact_words_path=config.solution_words,
        is_pdf=False,
    )

    return pd.DataFrame(
        [summarizer.scrape(summary) for summary in tqdm(filter_types(abstracts))]
    )


def fetch_abstracts_from_dataframe(target: pd.DataFrame) -> pd.DataFrame:
    """get_abstracts _summary_
    Args:
        target (pd.DataFrame): _description_
    """
    dois = target["doi"]
    abstracts = target["abstract"].tolist()

    summarizer = DocScraper(
        target_words_path=config.target_words,
        bycatch_words_path=config.bycatch_words,
        research_words_path=config.research_words,
        tech_words_path=config.tech_words,
        impact_words_path=config.solution_words,
        is_pdf=False,
    )

    return pd.DataFrame(
        [summarizer.scrape(summary) for summary in tqdm(filter_types(abstracts))]
    ).join(dois)
