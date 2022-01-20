r"""Contains methods that take various files, which each
return varying dataframes or directories for each"""

from fnmatch import fnmatch
from os import listdir, path

import pandas as pd
from tqdm import tqdm

from scrape.config import ScrapeConfig, read_config
from scrape.json import JSONScraper
from scrape.pdf import PDFScraper
from scrape.scraper import Scraper

@cache
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
    print(f"\n[sciscraper]: Getting entries from file: {target}")
    with open(target, newline="", encoding="utf-8") as f:
        df = list(pd.read_csv(f, usecols=["DOI"])["DOI"])
        search_terms = [
            search_text
            for search_text in df
            if isinstance(search_text, float) is False and search_text is not None
        ]
        scraper = JSONScraper(config.citations_dataset_url, False)
        return pd.DataFrame(
            [scraper.download(search_text) for search_text in tqdm(search_terms)]
        )

@cache
def fetch_terms_from_pubid(target: pd.DataFrame) -> pd.DataFrame:
    """fetch_terms_from_pubid reads a pandas DataFrame,
    takes the cited_dimensions_ids from the result of a prior fetch_terms_from_doi method
    scrapes the dimensions.ai API for each listed pub_id for each paper, and returns
    bibliographic information for each cited paper.

    Args:
        target (pd.DataFrame): A pandas dataframe.

    Returns:
        pd.DataFrame: a dataframe containing the
        bibliographic information for each of the provided citations
    """
    df = target.explode("cited_dimensions_ids", "title")
    scraper = JSONScraper(config.citations_dataset_url, False)
    search_terms = (
        search_text
        for search_text in df["cited_dimensions_ids"]
        if isinstance(search_text, float) is False and search_text is not None
    )
    src_title = pd.Series(df["title"])

    return pd.DataFrame(
        [scraper.download(search_text) for search_text in tqdm(list(search_terms))]
    ).join(src_title)

@cache
def fetch_citations_hence(target: pd.DataFrame) -> pd.DataFrame:
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
    search_terms = (
        search_text
        for search_text in target["id"]
        if isinstance(search_text, float) is False and search_text is not None
    )
    scraper = JSONScraper(config.url_dmnsns, True)
    return pd.DataFrame(
        [scraper.download(search_text) for search_text in tqdm(list(search_terms))]
    )

@cache
def fetch_terms_from_pdf_files(config: ScrapeConfig) -> pd.DataFrame:
    """fetch_terms_from_pdf_files goes into a directory, reads through
    each pdf file, parses the text, and then generates entries in a dataframe

    Args:
        config (ScrapeConfig): the directory to be parsed

    Returns:
        pd.DataFrame: the dataframe containing bibliographic data on each article.
    """

    search_terms = [
        path.join(config.paper_folder, file)
        for file in listdir(config.paper_folder)
        if fnmatch(path.basename(file), "*.pdf")
    ]
    scraper = PDFScraper(
        config.research_words, config.bycatch_words, config.target_words
    )
    return pd.DataFrame([scraper.scrape(file) for file in tqdm(search_terms)])
