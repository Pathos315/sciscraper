r"""Contains methods that take various files, which each
return varying dataframes or directories for each"""

from enum import Enum
from fnmatch import fnmatch
from os import listdir, path
from pathlib import Path
from typing import Any

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
        export: bool = True,
        get_citation: bool = True,
    ):
        self.target = target
        self.column = column
        self.config = config
        self.scrape_key = scrape_key
        self.filter_terms = filter_terms
        self.remove_empty = remove_empty
        self.export = export
        self.get_citation = get_citation

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
            "deriv": JSONScraper(self.config.citations_dataset_url, True),
        }

    def sciscrape(self) -> pd.DataFrame | None:
        scraper = self.scraper_dict[self.scrape_key]

        if self.scrape_key == "doi":
            search_terms: list[str] = unpack_csv(
                self.target, self.column.value, self.filter_terms  # type: ignore
            )
            dataframe = run_scrape(scraper, search_terms, desc="doi")

        elif self.scrape_key == "abstracts":
            search_terms = serialize_data(self.target, column="abstract")  # type: ignore
            self.subset_dict: dict[str, Any] = {
                "_doi": self.target["doi"],  # type: ignore
                "_title": self.target["title"],  # type: ignore
            }
            dataframe = run_scrape(
                scraper,
                search_terms,
                desc="abstracts",
                subset=pd.DataFrame(data=self.subset_dict),
            )

        elif self.scrape_key == "pub":
            data_frame: pd.DataFrame = self.target.explode(  # type: ignore
                "cited_dimensions_ids", "title"  # type: ignore
            )
            search_terms = serialize_data(data_frame, "cited_dimensions_ids")  # type: ignore
            dataframe = run_scrape(
                scraper,
                search_terms,
                desc="citation",
                subset=pd.Series(data_frame["title"]),
            )

        elif self.scrape_key == "pdfs":
            search_terms = [
                path.join(self.config.test_src, file)
                for file in listdir(self.config.test_src)
                if fnmatch(path.basename(file), "*.pdf")
            ]
            dataframe = run_scrape(scraper, search_terms, desc="file")

        elif self.scrape_key == "deriv":
            search_terms = serialize_data(self.target, Column.ID)  # type: ignore
            dataframe = run_scrape(scraper, search_terms, desc="derived papers")

        else:
            raise KeyError(f"Unknown scrape key: {self.scrape_key}")

        if self.export:
            return export_data(dataframe, self.config.export_dir)
        else:
            return dataframe


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
    subset: list | pd.DataFrame | pd.Series | None = None,
) -> pd.DataFrame:
    df = pd.DataFrame([scraper.scrape(term) for term in tqdm(search_terms, unit=desc)])
    if subset is not None:
        return df.join(subset, how="left", lsuffix="_source")
    return df


def serialize_data(
    target: pd.DataFrame, column: Column, remove_empty: bool = True
) -> list:
    series: pd.Series = target[column]  # type: ignore
    series_list = series.to_list()
    if remove_empty:
        return filter_types(series_list)
    return series_list


def unpack_csv(target: str | Path, column: Column, filtered: bool = True) -> list[str]:
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
            file_wrapper, skip_blank_lines=True, usecols=[column]  # type: ignore
        )[column]
        unfiltered_terms: list[str] = data_from_csv.drop_duplicates().to_list()
        if filtered:
            return filter_types(unfiltered_terms)
        return unfiltered_terms


def filter_neg_wordscores(
    target: pd.DataFrame, col: Column = Column.WORDSCORE
) -> pd.DataFrame:
    filt = target[col] > int(1)  # type: ignore
    return target.loc[filt]
