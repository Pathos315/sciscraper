import sys
from cProfile import Profile
import pstats
from subprocess import run as subp_run, Popen
from sciscraper.scrape.config import config, HOME, UTF
from sciscraper.scrape.fetch import SciScraper
from sciscraper.scrape.log import logger

venv_path = f"{HOME}/sciscraper/sciscraper"


def run_benchmark(args, sciscrape: SciScraper) -> None:
    with Profile() as pr:
        sciscrape(args.file, args.export, args.debug)
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    stats.dump_stats(config.profiling_path)
    Popen([sys.executable, "-m", "snakeviz", config.profiling_path])


def check_install() -> None:
    if sys.prefix == sys.base_prefix:
        logger.info(f"Activating sciscraper virtual environment at: {venv_path}")
        subp_run("source .venv/bin/activate")
    else:
        logger.info(f"sciscraper virtual environment already active at: {venv_path}")


def update_corpus_utility(bycatch: bool = False) -> None:

    corpus_kind = "BYCATCH" if bycatch else "TARGET"
    while True:
        try:
            term = input(
                f"Which word would you like to add to the {corpus_kind} words corpus?: "
            )
            base_url = f"https://relatedwords.org/api/related?term={term}"
            corpus_request(base_url, bycatch)
        except Exception:
            break


def corpus_request(base_url: str, bycatch: bool) -> None:
    from requests import get as req_get
    from json import loads

    filepath = config.bycatch_words if bycatch else config.target_words
    response = req_get(base_url)

    if response.status_code != 200:
        return None

    data = [entry for entry in loads(response.text) if entry["score"] >= 1.00]
    with open(filepath, "a", encoding=UTF) as file:
        for entry in data:
            file.write(f"{entry['word']}\n")


if __name__ == "__main__":
    update_corpus_utility()
