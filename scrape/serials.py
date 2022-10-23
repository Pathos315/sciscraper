from fnmatch import fnmatch
from functools import partial
from os import listdir, path

import pandas as pd

UTF = "utf-8"

def filter_types(target) -> list:
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

def serialize_from_csv(target: str, column: str="doi") -> list[str]:
    """serialize_from_csv reads a previously formatted .csv file of papers, identifies
        a specific column of interest, and returns a list of entries,
        with invalid fields either dropped or not.

    Args:
        target (str): the target .csv file as a pathname
        filtered (bool, optional): Either drop the invalid fields or not. Defaults to True.

    Returns:
        list[str]: A list of entries from the provided column."""
    with open(target, newline="", encoding=UTF) as file:
        data_from_csv: pd.Series = pd.read_csv(
            file, skip_blank_lines=True, usecols=[column]  # type: ignore
        ).drop_duplicates()[column]
        return filter_types(data_from_csv.to_list())

def serialize_from_series(target: pd.DataFrame, column: str="abstract") -> list[str]:
    return filter_types(target[column].to_list())

def serialize_from_array(target: pd.DataFrame, target_column_x:str="cited_dimensions_ids", target_column_y:str="title") -> tuple[list[str],list[str]]:
    """serialize_from_array reads a pandas DataFrame,
    takes the target_x param from the result of a prior fetch_terms_from_doi method
    scrapes the dimensions.ai API for each listed pub_id for each paper, and returns
    bibliographic information for each cited paper.
    Args:
        target (pd.DataFrame): A pandas dataframe.
    Returns:
        pd.DataFrame: a dataframe containing the
        bibliographic information for each of the provided citations
    """
    data_frame: pd.DataFrame = target.explode((target_column_x, target_column_y))
    return filter_types(data_frame[target_column_x].tolist()), filter_types(data_frame[target_column_y].tolist())

def serialize_from_directory(target:str, suffix: str="pdf") -> list[str]:
    return [path.join(target, file) for file in listdir(target) if fnmatch(path.basename(file), f"*.{suffix}")]

SERIALIZERS = {
    "DIRECTORY":serialize_from_directory,
    "ABSTRACTS": serialize_from_series,
    "DOI": serialize_from_csv,
    "REFERENCES": serialize_from_array,
    "TITLE_CSV": partial(serialize_from_csv, column="Name"),
    "DOI_SERIES": partial(serialize_from_series, column="doi")
}
