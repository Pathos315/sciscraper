""" utils.py governs the file creation processes for the sciscraper program.
"""
import random
import re
from contextlib import contextmanager
from datetime import date
from os import chdir, getcwd, makedirs, path

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

def export_data(dataframe: pd.DataFrame, export_dir: str | None=None):
    """Export data to the specified export directory.
    If it's a dataframe, then it returns a .csv file.
    """
    date_ = date.today().strftime("%y%m%d")
    logger.info(f"\n\n{dataframe.head(10)}")
    if export_dir:
        with change_dir(export_dir):
            print_id = random.randint(0, 100)
            export_name = f"{date_}_sciscraper_{print_id}.csv"
            logger.info(f"A spreadsheet was exported as {export_name} in {export_dir}.")
            if isinstance(dataframe, pd.DataFrame):
                dataframe.to_csv(export_name)


def guess_doi(pathname: str) -> str | None:
    """Guesses the digital identifier for the paper based on the filename"""
    DOI = re.compile(r"""(?xm)
    (?P<marker>         doi[:\/\s]{0,3})?
    (?P<prefix>
        (?P<namespace>  10)[.]
        (?P<registrant> \d{2,9})
    )
    (?P<sep>            [:\-\/\s\]])
    (?P<suffix>         [\-._;()\/:a-z0-9]+[a-z0-9])
    (?P<trailing>       ([\s\n\"<.]|$))
    """)

    match = DOI.search(pathname)
    if match:
        return match.group()
