from __future__ import annotations

from ast import literal_eval
from fnmatch import fnmatch
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

    Notes
    ----
    `literal_eval` is provided to account for when a json string
    gets read into the .csv file. literal_eval converts the string
    into a dict and then isolates the desired key from the dict.
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
            nested_terms.append(literal_eval(term)[column])
        else:
            initial_terms.append(term)
    return initial_terms + nested_terms
