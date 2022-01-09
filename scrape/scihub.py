import os
import time
from contextlib import suppress
from datetime import datetime
from typing import Generator

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from scrape.dir import change_dir
from scrape.log import log_msg


class SciHubScraper:
    """The SciHubScrape class takes the provided string from a prior list comprehension.
    Using that string value, it posts it to the selected website.
    Then, it downloads the ensuing pdf file that appears as a result of that query.
    """

    def __init__(self, scihub_url: str, research_dir: str) -> None:
        self.scihub_url = scihub_url
        self.sessions = requests.Session()
        self.now = datetime.now()
        self.date = self.now.strftime("%y%m%d")
        self.research_dir = os.path.realpath(f"{research_dir}_{self.date}")

    def download(self, search_text: str):
        """download generates a session and a payload
        This gets posted as a search query to the website.
        The search should return a pdf.
        Once the search is found, it is parsed with BeautifulSoup.
        Then, the link to download that pdf is isolated

        Args:
            search_text (str): the search query to be used.

        Returns:
            A pdf file.
        """
        print(
            f"[sciscraper]: Delving too greedily and too deep for download links for {search_text}, by means of dark and arcane magicx.",
            end="\r",
        )
        self.payload = {"request": f"{search_text}"}
        with change_dir(self.research_dir):
            time.sleep(1)
            with suppress(
                requests.exceptions.HTTPError, requests.exceptions.RequestException
            ):
                response = self.sessions.post(url=self.scihub_url, data=self.payload)
                response.raise_for_status()
                log_msg(str(response.status_code))
                soup = BeautifulSoup(response.text, "lxml")
                links = list(
                    ((item["onclick"]).split("=")[1]).strip("'")
                    for item in soup.select("button[onclick^='location.href=']")
                )
                return [self.enrich_scrape(search_text, link) for link in links]

    def enrich_scrape(self, search_text: str, link: str) -> None:
        """enrich_scrape goes to, and downloads, the isolated download link.
        It is sent as bytes to a temporary text file, as a middleman of sorts.
        The temporary text file is then used as a basis to generate a new pdf.
        The temporary text file is then deleted in preparation for the next pdf.

        Args:
            search_text (str): the link to be followed.
        """
        paper_url = f"{link}=true"
        paper_title = f'{self.date}_{search_text.replace("/","")}.pdf'
        time.sleep(1)
        paper_content = (
            requests.get(paper_url, stream=True, allow_redirects=True)
        ).content
        with open("temp_file.txt", "wb") as _tempfile:
            _tempfile.write(paper_content)
        with open(paper_title, "wb") as file:
            for line in open("temp_file.txt", "rb").readlines():
                file.write(line)
        os.remove("temp_file.txt")
