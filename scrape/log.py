import logging

logger = logging.getLogger("sciscraper")
logger.setLevel(level=logging.INFO)
datefmt = "%y-%m-%d %H:%M"
formatter = logging.Formatter("\n[sciscraper]: %(asctime)s - %(message)s\n")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

def logging_level(verbose):
    return logger.setLevel(logging.DEBUG) if verbose else logger.setLevel(logging.INFO)
