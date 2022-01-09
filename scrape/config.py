import json
from dataclasses import dataclass

@dataclass
class ScrapeConfig:
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
    with open(config_file, encoding="utf-8") as file:
        data = json.load(file)
        return ScrapeConfig(**data)
