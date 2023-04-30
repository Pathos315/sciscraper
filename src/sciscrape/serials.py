from __future__ import annotations

from json import JSONDecodeError
from json import loads as json_loads
from pathlib import Path
from typing import Any

import pandas as pd

from sciscrape.config import FilePath
from sciscrape.log import logger


def path_normalization(target: FilePath) -> Path:
    return Path(target) if not isinstance(target, Path) else target


def serialize_from_csv(target: FilePath, column: str = "doi") -> list[str]:
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
    list[str]:
        A list of entries from the provided column, `column`.
    """
    target = path_normalization(target)
    data: pd.DataFrame = (
        pd.read_csv(
            target,
            skip_blank_lines=True,
            usecols=[column],
        )
        .fillna("N/A")
    )
    data_list = clean_any_nested_columns(
        data[column].to_list(),
        column,
    )
    logger.debug("serializer=%s, terms=%s", serialize_from_csv, data_list)
    return data_list


def serialize_from_directory(target: FilePath, suffix: str = "pdf") -> list[str]:
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
    target = path_normalization(target)
    return [str(file) for file in target.glob(f'*.{suffix}')]


def clean_any_nested_columns(data_list: list[str], column: str) -> list[str]:
    initial_terms: list[str] = []
    nested_terms: list[str] = []
    for term in data_list:
        if "{" in term:
            loaded_term = grab_nested_terms(column, term)
            nested_terms.append(loaded_term) if loaded_term else None
        else:
            initial_terms.append(term)
    return initial_terms + nested_terms


def grab_nested_terms(column: str, term) -> Any:
    try:
        return dict(json_loads(term))[column]
    except JSONDecodeError:
        return None
