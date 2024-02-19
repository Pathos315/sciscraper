from __future__ import annotations

import re

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from json import loads
from time import sleep
from typing import TYPE_CHECKING
from typing import Any
from typing import override
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from bs4 import ResultSet
from requests import Response
from requests import Session
from selectolax.parser import HTMLParser
from selectolax.parser import Node

from src.config import DIMENSIONS_AI_KEYS
from src.config import config
from src.log import logger


if TYPE_CHECKING:
    from collections.abc import Generator

    from numpy import _SupportsItem


client = Session()


@dataclass(frozen=True)
class WebScrapeResult:
    """Represents a result from a scrape to be passed back to the dataframe."""

    title: str
    pub_date: str
    doi: str
    internal_id: str | None
    journal_title: str | None
    times_cited: int | None
    author_list: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    keywords: list[str] | None = field(default_factory=list)
    figures: list[str] | None = field(default_factory=list)
    biblio: str | None = None
    abstract: str | None = None


@dataclass
class WebScraper(ABC):
    """Abstract representation of a webscraper dataclass."""

    url: str
    sleep_val: float

    @abstractmethod
    def obtain(self, search_text: str) -> WebScrapeResult | None:
        """
        obtain takes the requested identifier string, `search_text`
        normally a digital object identifier (DOI), or similar,
        and requests it from the provided citational dataset,
        which returns bibliographic data on the paper(s) requested.

        Parameters
        ----------
        search_text : str
            the pubid or digital object identifier
            (i.e. DOI) of the paper in question

        Returns
        -------
        WebScrapeResult
            a dataclass containing the requested information,
            which gets sent back to a dataframe.
        """

    def get_items_from_response(self, response_text: str, key: str) -> Any:
        return loads(response_text)[key][0]

    def get_singular_item_from_response(
        self, response_text: str, key: str, subkey: str
    ) -> Any:
        doc = self.get_items_from_response(response_text, key)
        return doc[subkey]


@dataclass
class GoogleScholarScraper(WebScraper):
    """
    Representation of a webscraper that makes requests to Google Scholar.
    """

    start_year: int
    end_year: int
    publication_type: str
    num_articles: int

    @override
    def obtain(
        self, search_text: str
    ) -> Generator[WebScrapeResult, Any, None]:
        """
        Fetches and parses articles from Google Scholar based on the search_text and
        pre-defined criteria such as publication_type, date range, etc.
        """

        publication_type_mapping = {
            "all": "",
            "j": "source: journals",
            "b": "source: books",
            "c": "source: conferences",
            # Add more mappings as needed
        }
        publication_type = publication_type_mapping.get(
            self.publication_type, ""
        )
        num_pages = (self.num_articles - 1) // 10 + 1
        for page in range(num_pages):
            start = page * 10
            params_: _SupportsItem[Any] | None = {
                "q": search_text,
                "as_ylo": self.start_year,
                "as_yhi": self.end_year,
                f"{publication_type}": publication_type,
                "start": start,
            }  # type: ignore

            sleep(self.sleep_val)
            response = client.get(self.url, params=params_)  # type: ignore
            if not response.ok:
                logger.error(f"An error occurred for {search_text}")
                return

            soup = BeautifulSoup(response.text, "html.parser")
            results: ResultSet[Any] = soup.find_all("div", class_="gs_ri")

            for result in results:
                title_element = result.find("h3", class_="gs_rt")
                title = (
                    str(title_element.text).strip() if title_element else "N/A"
                )

                article_url_element = title_element.find("a")
                article_url = (
                    article_url_element["href"]
                    if article_url_element
                    else "N/A"
                )
                abstract = self.find_element_text(result, class_name="gs_rs")
                times_cited = self.find_element_text(
                    result, class_name="gs_flb", regex_pattern=r"\d+"
                )
                publication_year = self.find_element_text(
                    result, class_name="gs_a", regex_pattern=r"\d{4}"
                )
                yield WebScrapeResult(
                    title=title,
                    pub_date=publication_year,
                    doi=article_url,
                    internal_id=self.publication_type,
                    abstract=abstract,
                    times_cited=int(times_cited),
                    journal_title=None,
                    keywords=[search_text],
                )

    def find_element_text(
        self,
        result: Any,
        class_name: str,
        element: str = "div",
        regex_pattern: str | None = None,
    ) -> str:
        tag = result.find(element, class_=class_name)
        if not tag:
            return ""
        text: str = str(tag.text)
        if not regex_pattern:
            return text
        match = re.search(regex_pattern, text)
        return match.group(0) if match else ""


@dataclass
class DimensionsScraper(WebScraper):
    """
    Representation of a webscraper that makes requests to dimensions.ai.
    """

    query_subset_citations: bool = False
    sleep_val: float = 1.0

    def obtain(self, search_text: str) -> WebScrapeResult | None:
        querystring = self.create_querystring(search_text)
        response = self.get_docs(querystring)
        logger.debug(
            "search_text=%s, scraper=%r, status_code=%s",
            search_text,
            self,
            response.status_code,
        )

        if response.status_code != 200:
            return None

        data = self.enrich_response(response)
        return WebScrapeResult(**data)

    def get_docs(self, querystring: dict[Any, Any]) -> Response:
        sleep(self.sleep_val)
        return client.get(self.url, params=querystring)

    def enrich_response(self, response: Response) -> dict[str, Any]:
        api_keys = DIMENSIONS_AI_KEYS

        getters: dict[str, tuple[str, WebScraper]] = {
            "biblio": (
                "doi",
                CitationScraper(config.citation_crosscite_url, sleep_val=0.1),
            ),
            "abstract": (
                "internal_id",
                OverviewScraper(config.abstract_getting_url, sleep_val=0.1),
            ),
        }

        item = self.get_items_from_response(response.text, "docs")
        data = {key: item.get(value) for (key, value) in api_keys.items()}
        for key, getter in getters.items():
            data[key] = self.get_extra_variables(data, *getter)
        return data

    def get_extra_variables(
        self, data: dict[str, Any], query: str, getter: WebScraper
    ) -> WebScrapeResult | None:
        """get_extra_variables queries
        subsidiary scrapers to get
        additional data

        Parameters
        ----------
        data : dict
            the dict from the initial scrape
        getter : WebScraper
            the subsidiary scraper that
            will obtain additional information
        query : str
            the existing `data` to be queried.
        """
        try:
            return getter.obtain(data[query])
        except (KeyError, TypeError) as e:
            logger.error(
                "func_repr=%r, query=%s, error=%s, action_undertaken=%s",
                getter,
                query,
                e,
                "Returning None",
            )
            return None

    def create_querystring(self, search_text: str) -> dict[str, str]:
        return (
            {"or_subset_publication_citations": search_text}
            if self.query_subset_citations
            else {
                "search_mode": "content",
                "search_text": search_text,
                "search_type": "kws",
                "search_field": (
                    "doi" if search_text.startswith("10.") else "text_search"
                ),
            }
        )


class Style(Enum):
    """An enum that represents
    different academic writing styles.

    Parameters
    ----------
    Style : Enum
        A given academic writing style
    """

    APA = "apa"
    MLA = "modern-language-association"
    CHI = "chicago-fullnote-bibliography"


@dataclass
class CitationScraper(WebScraper):
    """
    CitationsScraper is a webscraper made exclusively for generating citations
    for requested papers.

    Attributes
    --------
    style : Style
        An Enum denoting a specific kind of writing style.
        Defaults to "apa".
    lang : str
        A string denoting which language will be requested.
        Defaults to "en-US".
    """

    style: Style = Style.APA
    lang: str = "en-US"

    @override
    def obtain(self, search_text: str) -> str | None:
        querystring = self.create_querystring(search_text)
        response = client.get(self.url, params=querystring)
        logger.debug(
            "search_text=%s, scraper=%r, status_code=%s",
            search_text,
            self,
            response.status_code,
        )
        return response.text if response.status_code == 200 else None

    def create_querystring(self, search_text: str) -> dict[str, Any]:
        return {
            "doi": search_text,
            "style": self.style.value,
            "lang": self.lang,
        }


@dataclass
class OverviewScraper(WebScraper):
    """
    OverviewScraper is a webscraper made exclusively
    for getting abstracts to papers
    within the dimensions.ai website.
    """

    @override
    def obtain(self, search_text: str) -> str | None:
        url = f"{self.url}/{search_text}/abstract.json"
        response = client.get(url)
        logger.debug(
            "search_text=%s, scraper=%r, status_code=%s",
            search_text,
            self,
            response.status_code,
        )

        return (
            self.get_singular_item_from_response(
                response.text,
                "docs",
                "abstract",
            )
            if response.status_code == 200
            else None
        )


# TODO: Figure out how to make requests to SemanticScholar without causing 429 Errors.
# Possibility of a post request according to their API?
@dataclass
class SemanticFigureScraper(WebScraper):
    """Scraper that queries
    semanticscholar.org for graphs and charts
    from the paper in question.
    """

    @override
    def obtain(self, search_text: str) -> list[str | None] | None:
        paper_url = self.find_paper_url(search_text)
        if paper_url is None:
            return None
        response = client.get(paper_url)
        logger.debug(
            "paper_url=%s, scraper=%r, status_code=%s",
            paper_url,
            self,
            response.status_code,
        )
        return (
            self.parse_html_tree(response.text)
            if response.status_code == 200
            else None
        )

    def find_paper_url(self, search_text: str) -> str | None:
        paper_searching_url = self.url + urlencode(
            {"query": search_text, "fields": "url", "limit": 1}
        )
        logger.info(paper_searching_url)
        paper_searching_response = client.get(paper_searching_url)
        logger.info(paper_searching_response)
        paper_info: dict[str, Any] = loads(paper_searching_response.text)
        logger.info(paper_info)
        try:
            paper_url: str | None = paper_info["data"][0]["url"]
            logger.debug("\n%s\n", paper_url)
        except IndexError as e:
            logger.error(
                "error=%s, action_undertaken=%s",
                e,
                "Returning None",
            )
            paper_url = None
        return paper_url

    def parse_html_tree(self, response_text: str) -> list[Any] | None:
        tree = HTMLParser(response_text)
        images: list[Node] = tree.css(
            "li.figure-list__figure > a > figure > div > img"
        )
        return (
            [image.attributes.get("src") for image in images]
            if images
            else None
        )
