from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from .config import UTF
from .log import logger


def serialize_from_txt(target: Path) -> List[str]:
    with open(target, encoding=UTF) as iowrapper:
        return [word.strip().lower() for word in iowrapper]


def serialize_from_csv(target: Path, column: str = "doi") -> List[str]:
    """
    serialize_from_csv
        Reads a .csv file of papers

    Reads a .csv file `target` identifies a specific
    column of interest `column` and then
    returns a list of entries.

    Parameters
    ---------
    target : Path
        The target .csv file, always as a pathname
    column : str
        The specific column of interest. Defaults to "doi".

    Returns
    -------
    List[str]:
        A list of entries from the provided column, `column`.

    """
    data: pd.DataFrame = pd.read_csv(target, skip_blank_lines=True, usecols=[column])
    data_list = list_with_na_replacement(data, column)
    cleaned_data = clean_any_nested_columns(data_list, column)
    logger.debug("serializer=%s, terms=%s", serialize_from_csv, cleaned_data)
    return cleaned_data


def serialize_from_directory(target: Path, suffix: str = "pdf") -> List[Path]:
    """
    serialize_directory takes a directory `target` and returns a list[str]
    of its contents to be scraped.

    Parameters
    ---------
    target : FilePath
        The target directory, always as a pathname.

    suffix: str
        The file extensions of interest. Defaults to "doi".

        Returns
    -------
    list[str]:
        A list of files from the provided directory, `target` that adhere
        to the requested format `suffix`.
    """
    data_list: List[Path] = list(target.rglob(f"*.{suffix}"))
    logger.debug("serializer=%s, terms=%s", serialize_from_directory, data_list)
    return data_list


def clean_any_nested_columns(data_list: List[str], column: str) -> List[str]:
    initial_terms: List[str] = [term for term in data_list if not term.startswith("{")]
    nested_terms: List[str] = [eval(term).get(column, "") for term in data_list if term.startswith("{")]
    return initial_terms + nested_terms



def list_with_na_replacement(dataframe: pd.DataFrame, column_name: str, _replacement_fill: str = "N/A",) -> list[str]:
    return dataframe[column_name].fillna(_replacement_fill).to_list()
