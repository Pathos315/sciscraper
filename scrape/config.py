import json
from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class ScrapeConfig:
    """A dataclass containing the overall configurations"""
    export_dir: str
    log_dir: str
    prime_src: str
    url_dmnsns: str
    research_dir: str
    url_scihub: str
    paper_folder: str
    research_words: str
    bycatch_words: str
    target_words: str


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
