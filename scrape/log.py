import logging
from datetime import datetime

now = datetime.now()
date = now.strftime("%y%m%d")

logger = logging.getLogger("sciscraper")
logger.setLevel(level=logging.INFO)
datefmt = "%d-%b-%y %H:%M:%S"
formatter = logging.Formatter("\n[sciscraper]: %(asctime)s - %(message)s\n")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
