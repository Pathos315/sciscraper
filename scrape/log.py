import logging
from datetime import datetime
from scrape.dir import change_dir
from scrape.config import read_config

now = datetime.now()
date = now.strftime("%y%m%d")
config = read_config("./config.json")
log_dir = config.log_dir 

with change_dir(log_dir):
    logging.basicConfig(
        filename=f"{date}_scraper.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )


def log_msg(msg: str) -> None:
    logging.info(msg)
    print(msg)
