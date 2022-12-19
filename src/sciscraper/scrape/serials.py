from fnmatch import fnmatch
from os import listdir, path
from ast import literal_eval
from typing import Any
import pandas as pd
from sciscraper.scrape.config import FilePath
from sciscraper.scrape.log import logger


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
    data: pd.DataFrame = pd.read_csv(target, skip_blank_lines=True, usecols=[column])
    data = data.fillna("N/A")
    data_list: list[Any] = data[column].to_list()
    data_list = clean_any_nested_columns(data_list)
    logger.debug("serializer=%s, terms=%s", repr(serialize_from_csv), data_list)
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
    data_list: list[str] = [
        path.join(target, file)
        for file in listdir(target)
        if fnmatch(path.basename(file), f"*.{suffix}")
    ]
    if len(data_list) == 0:
        raise ValueError("This directory contains no valid files.")

    logger.debug("serializer=%s, terms=%s", repr(serialize_from_directory), data_list)
    return data_list


def clean_any_nested_columns(data_list: list[Any]) -> list[Any]:
    return (
        [(list(dict(literal_eval(term)).values()))[0] for term in data_list]
        if "{" in data_list[1]
        else data_list
    )
