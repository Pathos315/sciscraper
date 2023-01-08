import logging

from sciscrape.change_dir import change_dir

logger = logging.getLogger("sciscraper")
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter("\n[sciscraper]: %(asctime)s - %(message)s\n")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

FILENAME = ".logs"

if logger.level == logging.DEBUG:
    with change_dir(FILENAME):
        doc_handler = logging.FileHandler("sciscraper.log")
        doc_handler.setFormatter(formatter)
        logger.addHandler(doc_handler)
