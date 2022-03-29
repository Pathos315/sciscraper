r"""Contains methods that take various files, which each
return varying dataframes or directories for each"""

from enum import Enum
from fnmatch import fnmatch
from os import listdir, path
from pathlib import Path
from typing import Any, Optional, Protocol

import pandas as pd
from tqdm import tqdm

from scrape.config import ScrapeConfig
from scrape.docscraper import DocScraper
from scrape.jsonscraper import JSONScraper
from scrape.utils import export_data


class Column(Enum):
    DOI = "doi"
    TITLE = "title"
    ABSTRACT = "abstract"
    ID = "id"
    CITED = "cited_dimensions_ids"
    WORDSCORE = "wordscore"


class SciScraper:
    def __init__(
        self,
        target: str | pd.DataFrame | Path,
        config: ScrapeConfig,
        scrape_key: str,
        column: Column | None = None,
        filter_terms: bool = True,
        remove_empty: bool = True,
    ):
        self.target = target
        self.column = column
        self.config = config
        self.scrape_key = scrape_key
        self.filter_terms = filter_terms
        self.remove_empty = remove_empty

    @property
    def scraper_dict(self) -> dict[str, Any]:
        return {
            "doi": JSONScraper(self.config.citations_dataset_url, False),
            "abstracts": DocScraper(
                target_words_path=self.config.target_words,
                bycatch_words_path=self.config.bycatch_words,
                research_words_path=self.config.research_words,
                tech_words_path=self.config.tech_words,
                impact_words_path=self.config.solution_words,
                is_pdf=False,
            ),
            "pub": JSONScraper(self.config.citations_dataset_url, False),
            "pdfs": DocScraper(
                target_words_path=self.config.target_words,
                bycatch_words_path=self.config.bycatch_words,
                research_words_path=self.config.research_words,
                tech_words_path=self.config.tech_words,
                impact_words_path=self.config.solution_words,
                is_pdf=True,
            ),
            "hence": JSONScraper(self.config.citations_dataset_url, True),
        }

    def sciscrape(self) -> pd.DataFrame:
        scraper = self.scraper_dict[self.scrape_key]

        if self.scrape_key == "doi":
            search_terms: list[str] = unpack_csv(
                self.target, self.column, self.filter_terms
            )
            return run_scrape(scraper, search_terms, desc="doi")

        elif self.scrape_key == "abstracts":
            search_terms = serialize_data(self.target, column="abstract")
            subset_dict: dict[str, Any] = {
                "_doi": self.target["doi"],
                "_title": self.target["title"],
            }
            subset: pd.DataFrame = pd.DataFrame(data=subset_dict)
            return run_scrape(scraper, search_terms, desc="abstracts", subset=subset)

        elif self.scrape_key == "pub":
            data_frame: pd.DataFrame = self.target.explode(
                "cited_dimensions_ids", "title"
            )
            search_terms = serialize_data(data_frame, "cited_dimensions_ids")
            subset: pd.Series = data_frame["title"]
            return run_scrape(scraper, search_terms, desc="citation", subset=subset)

        elif self.scrape_key == "pdfs":
            search_terms = [
                path.join(self.config.test_src, file)
                for file in listdir(self.config.test_src)
                if fnmatch(path.basename(file), "*.pdf")
            ]
            return run_scrape(scraper, search_terms, desc="file")

        elif self.scrape_key == "hence":
            search_terms = serialize_data(self.target, Column.ID)
            return run_scrape(scraper, search_terms, desc="derived papers")

        else:
            raise KeyError(f"Unknown scrape key: {self.scrape_key}")


###Constituent Functions###


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


def run_scrape(
    scraper: JSONScraper | DocScraper,
    search_terms: list,
    desc: str,
    subset: Optional[list | pd.DataFrame | pd.Series] = None,
) -> pd.DataFrame:
    df = pd.DataFrame([scraper.scrape(term) for term in tqdm(search_terms, unit=desc)])
    if subset is not None:
        return df.join(subset, how="left", lsuffix="_source")
    return df


def serialize_data(
    target: pd.DataFrame, column: Column, remove_empty: bool = True
) -> list:
    series: pd.Series = target[column]
    series_list = series.to_list()
    if remove_empty:
        return filter_types(series_list)
    return series_list


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
        if filtered:
            return filter_types(unfiltered_terms)
        return unfiltered_terms


def filter_neg_wordscores(
    target: pd.DataFrame, col: Column = Column.WORDSCORE
) -> pd.DataFrame:
    filt = target[col] > int(1)
    return target.loc[filt]


'''
def fetch_terms_from_csv(
    target: str, column: Column, config: ScrapeConfig
) -> pd.DataFrame:
    """fetch_terms_from_csv reads a csv file line by line,
    isolating digital object identifiers (DOIs),
    scrapes the web for each DOIs bibliographic data,
    and places all of that resulting data into a pandas dataframe.
    """
    search_terms: list[str] = unpack_csv(target, column)
    scraper = JSONScraper(config.citations_dataset_url, False)
    return run_scrape(scraper, search_terms, desc=column)


"""
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
"""
def fetch_terms_from_csv(
    target: str, column: Column, config: ScrapeConfig
) -> pd.DataFrame:
    """fetch_terms_from_csv reads a csv file line by line,
    isolating digital object identifiers (DOIs),
    scrapes the web for each DOIs bibliographic data,
    and places all of that resulting data into a pandas dataframe.
    """
    search_terms: list[str] = unpack_csv(target, column)
    scraper = JSONScraper(config.citations_dataset_url, False)
    return run_scrape(scraper, search_terms, desc=column)
    

def fetch_abstracts_from_dataframe(
    target: pd.DataFrame, column: Column, config: ScrapeConfig
) -> pd.DataFrame:
    """get_abstracts _summary_

    Args:
        target (pd.DataFrame): _description_
    """
    subset_dict: dict = {"_doi": target["doi"], "_title": target["title"]}
    subset: pd.DataFrame = pd.DataFrame(data=subset_dict)
    search_terms: list = serialize_data(target, column="abstract")

    scraper = DocScraper(
        target_words_path=config.target_words,
        bycatch_words_path=config.bycatch_words,
        research_words_path=config.research_words,
        tech_words_path=config.tech_words,
        impact_words_path=config.solution_words,
        is_pdf=False,
    )

    return run_scrape(scraper, search_terms, desc=column)


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
    subset: pd.Series = data_frame["title"]

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
    scraper = DocScraper(
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

    scraper = DocScraper(
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
'''
