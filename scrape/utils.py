""" utils.py governs the file creation processes for the sciscraper program.
"""
import os
import random
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import pandas as pd


@contextmanager
def change_dir(destination: str):
    """Sets a destination for exported files."""
    cwd = os.getcwd()
    try:
        __dest = os.path.realpath(destination)
        os.makedirs(__dest, exist_ok=True)
        os.chdir(__dest)
        yield
    finally:
        os.chdir(cwd)


def export_data(dataframe: Optional[pd.DataFrame], export_dir: str):
    """Export data to the specified export directory.
    If it's a dataframe, then it returns a .csv file.
    """
    now = datetime.now()
    date = now.strftime("%y%m%d")
    with change_dir(export_dir):
        print_id = random.randint(0, 100)
        export_name = f"{date}_DIMScrape_Refactor_{print_id}.csv"
        print(
            f"\n[sciscraper]: A spreadsheet was exported as {export_name} in {export_dir}.\n"
        )
        if isinstance(dataframe, pd.DataFrame):
            dataframe.to_csv(export_name)
            print(dataframe.head(10))
            print(dataframe.tail(10))
