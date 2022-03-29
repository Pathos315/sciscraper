from enum import Enum
from time import sleep

from requests import Session
from requests.exceptions import HTTPError

from scrape.log import logger


class Style(Enum):
    APA = "apa"
    MLA = "modern-language-association"
    CHI = "chicago-fullnote-bibliography"


class CitationGenerator:
    def __init__(
        self,
        doi: str,
        style: Style = "apa",
        url: str = "https://citation.crosscite.org/format",
        lang: str = "en-US",
    ):
        self.doi = doi
        self.style = style
        self.url = url
        self.sessions = Session()
        self.lang = lang

    def get_citation(self) -> str | None:
        querystring = {"doi": self.doi, "style": self.style, "lang": self.lang}

        sleep(1)

        request = self.sessions.get(self.url, params=querystring)
        try:
            request.raise_for_status()
            logger.debug(request.status_code)
            return request.text
        except (HTTPError) as http_error:
            logger.error(
                f"{http_error}occurred while generating the citation."
                f"Status Code: {request.status_code}"
                "Proceeding to next item in sequence."
            )
