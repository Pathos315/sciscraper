import logging
import sys
from datetime import datetime

from scrape.config import read_config
from scrape.utils import change_dir

now = datetime.now()
date = now.strftime("%y%m%d")
config = read_config("./config.json")
log_dir = config.log_dir

with change_dir(log_dir):
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format="%(asctime)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
