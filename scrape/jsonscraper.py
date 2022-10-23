from dataclasses import dataclass, field

## Scraping Related Imports
from requests import Session
from json import loads
from time import sleep

from scrape.log import logger

DIMENSIONS_AI_KEYS = {
    "title":"title",
    "pub_date":"pub_date",
    "doi":"doi",
    "internal_id":"id",
    "abstract":"abstract",
    "journal_title":"journal_title",
    "times_cited":"times_cited",
    "author_list":"author_list",
    "citations":"cited_dimensions_ids",
    "keywords":"mesh_terms"
}

SEMANTIC_SCHOLAR_KEYS = {
    "title":"title",
    "pub_date":"publicationDate",
    "doi":"externalIds",
    "internal_id":"externalIds",
    "abstract":"abstract",
    "journal_title":"journal",
    "times_cited":"citationCount",
    "author_list":"authors",
    "citations":"citations",
    "keywords":"s2FieldsOfStudy"
}

@dataclass(frozen=True, order=True)
class ScrapeResult:
    title: str
    pub_date: str
    doi: str
    internal_id: str|None
    abstract: str
    journal_title: str|None
    times_cited: int|None
    author_list: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    keywords: list[str]|None = field(default_factory=list)

@dataclass
class WebScraper:
    url: str
    query_subset_citations: bool = False
    api_keys: dict[str,str] = field(default_factory=dict)
    querystring: dict[str,str] = field(default_factory=dict)
    session: Session = field(default_factory=Session)

    def scrape(self, search_text: str) -> ScrapeResult | None:
        """download takes the requested pubid or DOI
        and requests it from the provided citational dataset,
        which returns bibliographic data on the paper(s) requested.

        Args:
            search_text (str): the pubid or DOI

        Returns:
            dict: a JSON entry, which gets sent back to a dataframe.
        """
        self.create_querystring(search_text)
        request = self.session.get(self.url, params=self.querystring)
        sleep(1.5)

        if request.status_code == 200:
            docs = loads(request.text)["docs"]
            item = docs[0]
            data = {key:item.get(value) for (key, value) in self.api_keys.items()}
            logger.debug(data)
            scrape = ScrapeResult(**data)
            logger.debug(scrape)
            return scrape

    def create_querystring(self, search_text: str):
        self.querystring = {"or_subset_publication_citations": search_text} if self.query_subset_citations else {
            "search_mode": "content",
            "search_text": search_text,
            "search_type": "kws",
            "search_field": "doi" if search_text.startswith("10") else "text_search",
            }

