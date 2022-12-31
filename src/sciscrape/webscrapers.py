from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import Enum
from time import sleep

from json import loads

from selectolax.parser import HTMLParser
from requests import Response, Session
from sciscrape.log import logger
from sciscrape.config import config


client = Session()

DIMENSIONS_AI_KEYS: dict[str, str] = {
    "title": "title",
    "pub_date": "pub_date",
    "doi": "doi",
    "internal_id": "id",
    "journal_title": "journal_title",
    "times_cited": "times_cited",
    "author_list": "author_list",
    "citations": "cited_dimensions_ids",
    "keywords": "mesh_terms",
}


@dataclass(slots=True, frozen=True, order=True)
class WebScrapeResult:
    """Represents a result from a scrape to be passed back to the dataframe."""

    title: str
    pub_date: str
    doi: str
    internal_id: Optional[str]
    journal_title: Optional[str]
    times_cited: Optional[int]
    author_list: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    keywords: Optional[list[str]] = field(default_factory=list)
    figures: Optional[list[str]] = field(default_factory=list)
    biblio: Optional[str] = None
    abstract: Optional[str] = None

    @classmethod
    def from_dict(cls, dict_input: dict):
        return WebScrapeResult(**dict_input)

    def to_dict(self):
        return asdict(self)


@dataclass(slots=True)
class WebScraper(ABC):
    """Abstract representation of a webscraper dataclass."""

    url: str
    sleep_val: float = config.sleep_interval

    @abstractmethod
    def obtain(self, search_text: str) -> Optional[WebScrapeResult]:
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
        return (loads(response_text)[key])[0]

    def get_singular_item_from_response(
        self, response_text: str, key: str, subkey: str
    ) -> Any:
        doc = self.get_items_from_response(response_text, key)
        return doc[subkey]


@dataclass(slots=True)
class DimensionsScraper(WebScraper):
    """
    Representation of a webscraper that makes requests to dimensions.ai.
    This is sciscraper's preferred webscraper.
    """

    query_subset_citations: bool = False

    def obtain(self, search_text: str) -> Optional[WebScrapeResult]:
        querystring: dict[str, str] = self.create_querystring(search_text)
        response = self.get_docs(querystring)
        logger.debug(
            "search_text=%s, scraper=%s, status_code=%s",
            search_text,
            repr(self),
            response.status_code,
        )

        if response.status_code != 200:
            return None

        data = self.enrich_response(response)
        return WebScrapeResult(**data)

    def get_docs(self, querystring) -> Response:
        sleep(self.sleep_val)
        return client.get(self.url, params=querystring)

    def enrich_response(self, response: Response) -> dict[str, Any]:
        api_keys: dict[str, str] = DIMENSIONS_AI_KEYS

        getters: dict[str, tuple[str, WebScraper]] = {
            "biblio": (
                "doi",
                CitationScraper(config.citation_crosscite_url, sleep_val=0.1),
            ),
            "abstract": (
                "internal_id",
                OverviewScraper(config.abstract_getting_url, sleep_val=0.1),
            ),
            "figures": (
                "title",
                SemanticFigureScraper(config.semantic_scholar_url_stub, sleep_val=0.1),
            ),
        }

        item = self.get_items_from_response(response.text, "docs")
        data: dict[str, Any] = {
            key: item.get(value) for (key, value) in api_keys.items()
        }
        for key, getter in getters.items():
            data[key] = self.get_extra_variables(data, getter[0], getter[1])
        return data

    def get_extra_variables(
        self, data: dict[str, Any], query: str, getter: WebScraper
    ) -> Optional[WebScrapeResult]:
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
            logger.debug(
                "func_repr=%s, query=%s, error=%s, action_undertaken=%s",
                repr(getter),
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
                "search_field": "doi"
                if search_text.startswith("10.")
                else "text_search",
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


@dataclass(slots=True)
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

    def obtain(self, search_text: str) -> Optional[str]:
        querystring: dict[str, Any] = self.create_querystring(search_text)
        response: Response = client.get(self.url, params=querystring)
        logger.debug(
            "search_text=%s, scraper=%s, status_code=%s",
            search_text,
            repr(self),
            response.status_code,
        )
        return None if response.status_code != 200 else response.text

    def create_querystring(self, search_text) -> dict[str, Any]:
        return {
            "doi": search_text,
            "style": self.style.value,
            "lang": self.lang,
        }


@dataclass(slots=True)
class OverviewScraper(WebScraper):
    """
    OverviewScraper is a webscraper made exclusively
    for getting abstracts to papers
    within the dimensions.ai website.
    """

    def obtain(self, search_text: str) -> Optional[str]:
        url: str = f"{self.url}/{search_text}/abstract.json"
        response: Response = client.get(url)
        logger.debug(
            "search_text=%s, scraper=%s, status_code=%s",
            search_text,
            repr(self),
            response.status_code,
        )

        return (
            None
            if response.status_code != 200
            else self.get_singular_item_from_response(
                response.text,
                "docs",
                "abstract",
            )
        )


@dataclass(slots=True)
class SemanticFigureScraper(WebScraper):
    """Scraper that queries
    semanticscholar.org for graphs and charts
    from the paper in question.
    """

    def obtain(self, search_text: str) -> Optional[list[Optional[str]]]:
        paper_url = self.find_paper_url(search_text)
        if paper_url is None:
            return None
        response: Response = client.get(paper_url)
        logger.debug(
            "paper_url=%s, scraper=%s, status_code=%s",
            paper_url,
            repr(self),
            response.status_code,
        )
        return (
            None if response.status_code != 200 else self.parse_html_tree(response.text)
        )

    def find_paper_url(self, search_text: str) -> Optional[str]:
        title = search_text.replace(" ", "+")
        paper_searching_url = f"{self.url}{title}&fields=url&limit=1"
        paper_searching_response: Response = client.get(paper_searching_url)
        paper_info: dict[str, Any] = loads(paper_searching_response.text)
        try:
            paper_url: Optional[str] = paper_info["data"][0]["url"]
            logger.debug(f"\n{paper_url}\n")
        except IndexError as e:
            logger.debug(
                "error=%s, action_undertaken=%s",
                e,
                "Returning None",
            )
            paper_url = None
        return paper_url

    def parse_html_tree(self, response_text: str) -> Optional[list[Any]]:
        tree: HTMLParser = HTMLParser(response_text)
        images: list[Any] = tree.css("li.figure-list__figure > a > figure > div > img")
        return [image.attributes.get("src") for image in images] if images else None
