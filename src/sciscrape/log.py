import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from sciscrape.change_dir import change_dir

logger = logging.getLogger("sciscraper")
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter("\n[sciscraper]: %(asctime)s - %(message)s\n")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

LOGDIR = Path(".logs").resolve()

if logger.level == logging.DEBUG:
    with change_dir(LOGDIR):
        doc_handler = RotatingFileHandler(
            "sciscraper.log",
            maxBytes=10,
            backupCount=5,
        )
        doc_handler.setFormatter(formatter)
        logger.addHandler(doc_handler)
