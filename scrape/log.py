import logging

logger = logging.getLogger("sciscraper")
logger.setLevel(level=logging.INFO)
datefmt = "%y-%m-%d %H:%M:%S"
formatter = logging.Formatter("\n[sciscraper]: %(asctime)s - %(message)s\n")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
