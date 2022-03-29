from json import loads
from json.decoder import JSONDecodeError
from time import sleep

## Scraping Related Imports
from requests import Session
from requests.exceptions import HTTPError

from scrape.log import logger
from scrape.scraper import ScrapeResult


class JSONScraper:
    """The JSONScraper class takes the provided string from a prior list comprehension.
    Using that string value, it gets the resulting JSON data, parses it,
    and then returns a dictionary, which gets appended to a list.
    """

    def __init__(
        self, citations_dataset_url: str, query_subset_citations: bool
    ) -> None:
        self.citations_dataset_url = citations_dataset_url
        self.sessions = Session()
        self.search_field = ""
        self.query_subset = query_subset_citations
        self.docs = []
        self.data = {}

    def specify_search(self, search_text: str) -> str:
        """Determines whether the dimensions.ai
        query will be for either
        a full_search or just for the doi.
        """
        self.search_field = "doi" if search_text.startswith("10") else "full_search"
        return self.search_field

    def scrape(self, search_text: str):
        """download takes the requested pubid or DOI
        and requests it from the provided citational dataset,
        which returns bibliographic data on the paper(s) requested.

        Args:
            search_text (str): the pubid or DOI

        Returns:
            dict: a JSON entry, which gets sent back to a dataframe.
        """

        if self.query_subset:
            querystring = {"or_subset_publication_citations": search_text}
        else:
            self.search_field = self.specify_search(search_text)
            querystring = {
                "search_mode": "content",
                "search_text": search_text,
                "search_type": "kws",
                "search_field": self.search_field,
            }

        sleep(1.5)

        request = self.sessions.get(self.citations_dataset_url, params=querystring)
        try:
            request.raise_for_status()
            logger.debug(request.status_code)
            self.docs = loads(request.text)["docs"]

        except (JSONDecodeError, HTTPError) as parse_error:
            logger.error(
                f"An error occurred while searching for {search_text}."
                f"Status Code: {request.status_code}"
                "Proceeding to next item in sequence."
                f"Cause of error: {parse_error}"
            )

        item = self.docs[0]
        return ScrapeResult(
            title=item["title"],
            author_list=item["author_list"],
            cited_dimensions_ids=item["cited_dimensions_ids"],
            times_cited=item["times_cited"],
            publisher=item["publisher"],
            pub_date=item["pub_date"],
            doi=item["doi"],
            pub_id=item["id"],
            abstract=item["abstract"],
            journal_title=item["journal_title"],
            volume=item["volume"],
            issue=item["issue"],
            mesh_terms=item["mesh_terms"],
        )
