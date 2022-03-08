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
from scrape.pdf import PaperSummarizer, PDFScraper


class Column(Enum):
    DOI = "doi"
    TITLE = "title"
    ABSTRACT = "abstract"


def filter_types(data) -> list[str]:
    """filter_types _summary_

    Args:
        data (_type_): _description_

    Returns:
        list[str]: _description_
    """
    return [i for i in data if not isinstance(i, (type(None), float))]


def unpack_csv(target: str, column: Column) -> list[str]:
    """unpack_csv _summary_

    Args:
        _target (str): _description_
        _colsinuse (str): _description_

    Returns:
        list[str]: _description_
    """
    with open(target, newline="", encoding="utf-8") as file_wrapper:
        return (
            pd.read_csv(
                file_wrapper,
                skip_blank_lines=True,
                usecols=[column],
            )[column]
            .drop_duplicates()
            .tolist()
        )


def fetch_terms_from_csv(
    target: str, column: str, config: ScrapeConfig
) -> pd.DataFrame:
    """fetch_terms_from_doi reads a csv file line by line,
    isolating digital object identifiers (DOIs),
    scrapes the web for each DOIs bibliographic data,
    and places all of that resulting data into a pandas dataframe.
    """
    data_frame = unpack_csv(target, column)
    search_terms = filter_types(data_frame)
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
    dois = target["doi"]
    abstracts = target["abstract"].tolist()

    summarizer = PaperSummarizer(
        target_path=config.target_words,
        bycatch_path=config.bycatch_words,
        research_path=config.research_words,
        digi_path=config.tech_words,
        solutions_path=config.solution_words,
    )

    return pd.DataFrame(
        [
            summarizer.analyze(summary)
            for summary in tqdm(filter_types(abstracts), unit="abstract")
        ]
    ).join(dois)


def fetch_terms_from_pubid(target: pd.DataFrame, config: ScrapeConfig) -> pd.DataFrame:
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
    data_frame = target.explode(("cited_dimensions_ids", "title"))
    search_terms = filter_types(data_frame["cited_dimensions_ids"])
    scraper = JSONScraper(config.citations_dataset_url, False)
    src_title = data_frame["title"]

    return pd.DataFrame(
        [
            scraper.download(search_text)
            for search_text in tqdm(search_terms, unit="citation")
        ]
    ).join(src_title)


def fetch_citations_hence(target: pd.DataFrame, config: ScrapeConfig) -> pd.DataFrame:
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
    search_terms = filter_types(target["id"])
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
        pd.DataFrame: the dataframe containing bibliographic data on each article.
    """

    search_terms = [
        path.join(config.test_src, file)
        for file in listdir(config.test_src)
        if fnmatch(path.basename(file), "*.pdf")
    ]
    scraper = PDFScraper(
        target_path=config.target_words,
        bycatch_path=config.bycatch_words,
        research_path=config.research_words,
        digi_path=config.tech_words,
        solutions_path=config.solution_words,
    )
    return pd.DataFrame(
        [scraper.analyze(file) for file in tqdm(search_terms, unit="file")]
    )


def fetch_abstracts_from_csv(target: str, config: ScrapeConfig) -> pd.DataFrame:
    """get_abstracts _summary_

    Args:
        target (pd.DataFrame): _description_
    """
    abstracts: list[str] = unpack_csv(target, "abstract")

    summarizer = PaperSummarizer(
        target_path=config.target_words,
        bycatch_path=config.bycatch_words,
        research_path=config.research_words,
        digi_path=config.tech_words,
        solutions_path=config.solution_words,
    )

    return pd.DataFrame(
        [
            summarizer.analyze(summary)
            for summary in tqdm(filter_types(abstracts), unit="abstract")
        ]
    )
