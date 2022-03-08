import json
from time import sleep
from json.decoder import JSONDecodeError

## Scraping Related Imports
from requests import Session
from requests.exceptions import HTTPError
from scrape.log import logger


class JSONScraper:
    """The JSONScrape class takes the provided string from a prior list comprehension.
    Using that string value, it gets the resulting JSON data, parses it,
    and then returns a dictionary, which gets appended to a list.
    """

    def __init__(self, citations_dataset_url: str, subset_query: bool) -> None:
        self.citations_dataset_url = citations_dataset_url
        self.sessions = Session()
        self.search_field = ""
        self.subset_query = subset_query
        self.docs = []
        self.data = {}

    def download(self, search_text: str) -> dict:
        """download takes the requested pubid or DOI
        and requests it from the provided citational dataset,
        which returns bibliographic data on the paper(s) requested.

        Args:
            search_text (str): the pubid or DOI

        Returns:
            dict: a JSON entry, which gets sent back to a dataframe.
        """

        if self.subset_query:
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

        try:
            request = self.sessions.get(self.citations_dataset_url, params=querystring)
            request.raise_for_status()
            logger.debug(request.status_code)
            self.docs = loads(request.text)["docs"]

        except (JSONDecodeError, HTTPError) as parse_error:
            logger.error(
                f"An error occurred while searching for {search_text}.\
                Status Code: {request.status_code}\
                Proceeding to next item in sequence.\
                Cause of error: {parse_error}"

        for item in self.docs:
            self.data = self.get_data_entry(
                item,
                keys=[
                    "title",
                    "author_list",
                    "publisher",
                    "pub_date",
                    "doi",
                    "id",
                    "abstract",
                    "acknowledgements",
                    "journal_title",
                    "volume",
                    "issue",
                    "times_cited",
                    "mesh_terms",
                    "cited_dimensions_ids",
                ],
            )
        return self.data

    def specify_search(self, search_text: str) -> str:
        """Determines whether the dimensions.ai
        query will be for either
        a full_search or just for the doi.
        """
        self.search_field = (
            "doi" if str(search_text).startswith("10") else "full_search"
        )
        return self.search_field

    def get_data_entry(self, item, keys: list) -> dict:
        """Based on a provided list of keys and items in the JSON data,
        generates a dictionary entry.
        """
        return {_key: item.get(_key, "") for _key in keys}
