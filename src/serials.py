from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from src.config import UTF
from src.log import logger


if TYPE_CHECKING:
    from pathlib import Path


def serialize_from_txt(target: Path) -> list[str]:
    with open(target, encoding=UTF) as iowrapper:
        return [word.strip().lower() for word in iowrapper]


def serialize_from_csv(target: Path, column: str = "doi") -> list[str]:
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
    data: pd.DataFrame = pd.read_csv(
        target, skip_blank_lines=True, usecols=[column]
    )
    data_list = list_with_na_replacement(data, column)
    cleaned_data = clean_any_nested_columns(data_list, column)
    logger.debug("serializer=%s, terms=%s", serialize_from_csv, cleaned_data)
    return cleaned_data


def serialize_from_directory(target: Path, suffix: str = "pdf") -> list[Path]:
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
    data_list: list[Path] = list(target.rglob(f"*.{suffix}"))
    logger.debug(
        "serializer=%s, terms=%s", serialize_from_directory, data_list
    )
    return data_list


def clean_any_nested_columns(data_list: list[str], column: str) -> list[str]:
    initial_terms: list[str] = [
        term for term in data_list if not term.startswith("{")
    ]
    nested_terms: list[str] = [
        eval(term).get(column, "")
        for term in data_list
        if term.startswith("{")
    ]
    return initial_terms + nested_terms


def list_with_na_replacement(
    dataframe: pd.DataFrame,
    column_name: str,
    _replacement_fill: str = "N/A",
) -> list[str]:
    return dataframe[column_name].fillna(_replacement_fill).to_list()
