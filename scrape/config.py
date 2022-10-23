r"""config contains the dataclass describing
    the overall configurations
    and a method to read the config

    Returns:
        a function that reads the dataclass as a JSON object.
    """

import json
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class ScrapeConfig:
    """A dataclass containing the overall configurations"""

    prog: str
    description: str
    export_dir: str
    demo_dir: str
    log_dir: str
    prime_src: str
    citations_dataset_url: str
    semantic_scholar_url_stub: str
    research_dir: str
    downloader_url: str
    test_src: str
    target_words: str
    bycatch_words: str


def read_config(config_file: str) -> ScrapeConfig:
    """read_config takes a .json file and returns a ScrapeConfig object.

    Args:
        config_file (str): the path to the .json file containing the configs.

    Returns:
        ScrapeConfig: A dataclass containing the overall configurations
    """
    with open(config_file, encoding="utf-8") as file:
        data = json.load(file)
        return ScrapeConfig(**data)
