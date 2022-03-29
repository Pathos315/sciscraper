""" utils.py governs the file creation processes for the sciscraper program.
"""
import random
from contextlib import contextmanager
from datetime import date
from os import chdir, getcwd, makedirs, path
from typing import Optional
import pandas as pd

from scrape.log import logger


@contextmanager
def change_dir(destination: str):
    """Sets a destination for exported files."""
    cwd = getcwd()
    try:
        dest = path.realpath(destination)
        makedirs(dest, exist_ok=True)
        chdir(dest)
        yield
    finally:
        chdir(cwd)


def export_data(dataframe: Optional[pd.DataFrame], export_dir: str):
    """Export data to the specified export directory.
    If it's a dataframe, then it returns a .csv file.
    """
    date_ = date.today().strftime("%y%m%d")
    with change_dir(export_dir):
        print_id = random.randint(0, 100)
        export_name = f"{date_}_sciscraper_{print_id}.csv"
        logger.info(f"A spreadsheet was exported as {export_name} in {export_dir}.")
        if isinstance(dataframe, pd.DataFrame):
            dataframe.to_csv(export_name)
            logger.info(f"\n\n{dataframe.head(10)}")
            logger.info(f"\n\n{dataframe.tail(10)}")
