from __future__ import annotations

from fnmatch import fnmatch
from json import loads as json_loads
from os import listdir, path

import pandas as pd

from sciscrape.config import FilePath
from sciscrape.log import logger


def serialize_from_csv(target: FilePath, column: str = "doi") -> list[str]:
    """
    serialize_from_csv
        Reads a .csv file of papers

    Reads a .csv file `target` identifies a specific
    column of interest `column` and then
    returns a list of entries.

    Parameters
    ---------
    target : FilePath
        The target .csv file, always as a pathname
    column : str
        The specific column of interest. Defaults to "doi".

    Returns
    -------
    list[str]:
        A list of entries from the provided column, `column`.
    """
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
    data_list = [
        path.join(target, file)
        for file in listdir(target)
        if fnmatch(path.basename(file), f"*.{suffix}")
    ]
    if not data_list:
        raise ValueError("This directory contains no valid files.")

    logger.debug("serializer=%s, terms=%s", serialize_from_directory, data_list)
    return data_list


def clean_any_nested_columns(data_list: list[str], column: str) -> list[str]:
    initial_terms: list[str] = []
    nested_terms: list[str] = []
    for term in data_list:
        if term.startswith("{"):
            loaded_term = json_loads(term)[column]
            nested_terms.append(loaded_term)
        else:
            initial_terms.append(term)
    return initial_terms + nested_terms
