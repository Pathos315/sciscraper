import json
from json.decoder import JSONDecodeError
from time import sleep

## Scraping Related Imports
import requests
from requests.exceptions import HTTPError


class JSONScraper:
    """The JSONScrape class takes the provided string from a prior list comprehension.
    Using that string value, it gets the resulting JSON data, parses it,
    and then returns a dictionary, which gets appended to a list.
    """

    def __init__(self, citations_dataset_url: str, subset_query: bool) -> None:
        self.citations_dataset_url = citations_dataset_url
        self.sessions = requests.Session()
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

        print(
            f"[sciscraper]: Searching for {search_text} via a {self.search_field}-style search.",
            end="\r",
        )
        if self.subset_query:
            querystring = {"or_subset_publication_citations": search_text}
        else:
            self.search_field = self.specify_search(search_text)
            querystring = {
                "search_mode": "content",
                "search_text": f"{search_text}",
                "search_type": "kws",
                "search_field": f"{self.search_field}",
            }

        sleep(1.5)

        try:
            request = self.sessions.get(self.citations_dataset_url, params=querystring)
            request.raise_for_status()
            print(str(request.status_code))
            self.docs = json.loads(request.text)["docs"]

        except (JSONDecodeError, HTTPError) as error:
            print(
                f"\n[sciscraper]: An error occurred while searching for {search_text}."
                "\n[sciscraper]: Proceeding to next item in sequence."
                f"Cause of error: {error}\n"
            )

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

    def specify_search(self, _search_text: str) -> str:
        """Determines whether the dimensions.ai
        query will be for either
        a full_search or just for the doi.
        """
        self.search_field = (
            "full_search" if str(_search_text).startswith("pub") else "doi"
        )
        return self.search_field

    def get_data_entry(self, item, keys: list) -> dict:
        """Based on a provided list of keys and items in the JSON data,
        generates a dictionary entry.
        """
        return {_key: item.get(_key, "") for _key in keys}
