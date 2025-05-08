"""
Web scraping functionality for academic data sources.

This module provides classes for extracting structured data from various
academic web services and APIs, handling authentication, rate limiting,
and data parsing.
"""

from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)
from urllib.parse import quote_plus, urlencode

from src.exceptions import DataProcessingError, NetworkError
from src.http_client import HttpClient, Response
from src.log import logger


@dataclass
class Author:
    """Represents an author of a scholarly work."""

    name: str
    """Author's full name."""

    id: str = ""
    """Author's identifier (e.g., ORCID ID, Semantic Scholar ID)."""

    affiliation: str = ""
    """Author's institutional affiliation."""

    email: str = ""
    """Author's email address."""


@dataclass
class Publication:
    """Represents a scholarly publication with standardized metadata."""

    title: str
    """Publication title."""

    authors: List[Author] = field(default_factory=list)
    """List of authors."""

    publication_date: str = ""
    """Date of publication (ISO format if available)."""

    doi: str = ""
    """Digital Object Identifier."""

    abstract: str = ""
    """Publication abstract."""

    journal: str = ""
    """Journal or venue name."""

    citations_count: int = 0
    """Number of citations."""

    citations: List[str] = field(default_factory=list)
    """List of citing publication titles or IDs."""

    references: List[str] = field(default_factory=list)
    """List of referenced publication titles or IDs."""

    keywords: List[str] = field(default_factory=list)
    """Keywords or research fields."""

    figures: List[str] = field(default_factory=list)
    """URLs or IDs of figures in the publication."""

    internal_id: str = ""
    """Source-specific identifier (e.g., Semantic Scholar ID)."""

    url: str = ""
    """URL to the publication."""

    full_text_url: str = ""
    """URL to access the full text."""

    biblio: str = ""
    """Bibliographic information in a structured format."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Publication:
        """
        Create a Publication from a dictionary.

        Args:
            data: Dictionary with publication data

        Returns:
            A Publication instance
        """
        # Extract basic fields with defaults
        title = data.get("title", "")

        # Create the publication
        pub = cls(title=title)

        # Set optional fields if present
        if "publication_date" in data:
            pub.publication_date = data["publication_date"]
        if "doi" in data:
            pub.doi = data["doi"]
        if "abstract" in data:
            pub.abstract = data["abstract"]
        if "journal" in data:
            pub.journal = data["journal"]
        if "citations_count" in data:
            pub.citations_count = data["citations_count"]
        if "internal_id" in data:
            pub.internal_id = data["internal_id"]
        if "url" in data:
            pub.url = data["url"]
        if "full_text_url" in data:
            pub.full_text_url = data["full_text_url"]
        if "biblio" in data:
            pub.biblio = data["biblio"]

        # Set list fields
        if "authors" in data and isinstance(data["authors"], list):
            pub.authors = [
                (
                    Author(name=author["name"])
                    if isinstance(author, dict)
                    else Author(name=str(author))
                )
                for author in data["authors"]
            ]

        if "citations" in data and isinstance(data["citations"], list):
            pub.citations = data["citations"]

        if "references" in data and isinstance(data["references"], list):
            pub.references = data["references"]

        if "keywords" in data and isinstance(data["keywords"], list):
            pub.keywords = data["keywords"]

        if "figures" in data and isinstance(data["figures"], list):
            pub.figures = data["figures"]

        return pub

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Publication to a dictionary.

        Returns:
            Dictionary representation of the Publication
        """
        return {
            "title": self.title,
            "authors": [
                {
                    "name": author.name,
                    "id": author.id,
                    "affiliation": author.affiliation,
                }
                for author in self.authors
            ],
            "publication_date": self.publication_date,
            "doi": self.doi,
            "abstract": self.abstract,
            "journal": self.journal,
            "citations_count": self.citations_count,
            "citations": self.citations,
            "references": self.references,
            "keywords": self.keywords,
            "figures": self.figures,
            "internal_id": self.internal_id,
            "url": self.url,
            "full_text_url": self.full_text_url,
            "biblio": self.biblio,
        }


class WebScraper(ABC):
    """
    Base class for web scrapers that fetch and parse academic data.

    This abstract class defines the interface for all web scrapers
    and provides common functionality.
    """

    def __init__(
        self,
        base_url: str,
        http_client: Optional[HttpClient] = None,
        rate_limit: float = 1.0,
    ):
        """
        Initialize the web scraper.

        Args:
            base_url: Base URL for API requests
            http_client: HTTP client for making requests
            rate_limit: Minimum time between requests in seconds
        """
        self.base_url = base_url
        self.http_client = http_client or HttpClient(base_url=base_url)
        self.rate_limit = rate_limit
        self.last_request_time = 0.0

    def search(self, query: str) -> Generator[Publication, None, None]:
        """
        Search for publications matching the query.

        Args:
            query: Search query

        Returns:
            Generator of Publication objects

        Raises:
            NetworkError: If the request fails
            DataProcessingError: If the response cannot be processed
        """
        try:
            # Apply rate limiting
            self._respect_rate_limit()

            # Format the request URL
            url = self._format_search_url(query)

            # Make the request
            response = self.http_client.get(url)

            # Process the response
            yield from self._process_search_response(response, query)

        except Exception as e:
            if isinstance(e, (NetworkError, DataProcessingError)):
                raise
            raise DataProcessingError(f"Search failed: {e}") from e

    def fetch_publication(self, identifier: str) -> Optional[Publication]:
        """
        Fetch a specific publication by its identifier.

        Args:
            identifier: Publication identifier (DOI, internal ID, etc.)

        Returns:
            Publication object if found, otherwise None

        Raises:
            NetworkError: If the request fails
            DataProcessingError: If the response cannot be processed
        """
        try:
            # Apply rate limiting
            self._respect_rate_limit()

            # Format the request URL
            url = self._format_publication_url(identifier)

            # Make the request
            response = self.http_client.get(url)

            # Process the response
            return self._process_publication_response(response, identifier)

        except Exception as e:
            if isinstance(e, (NetworkError, DataProcessingError)):
                raise
            raise DataProcessingError(
                f"Failed to fetch publication {identifier}: {e}"
            ) from e

    def _respect_rate_limit(self) -> None:
        """
        Ensure rate limiting by waiting if necessary.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_request
            logger.debug(
                f"Rate limiting: sleeping for {sleep_time:.2f} seconds"
            )
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    @abstractmethod
    def _format_search_url(self, query: str) -> str:
        """
        Format the URL for a search request.

        Args:
            query: Search query

        Returns:
            Formatted URL
        """
        pass

    @abstractmethod
    def _format_publication_url(self, identifier: str) -> str:
        """
        Format the URL for a publication request.

        Args:
            identifier: Publication identifier

        Returns:
            Formatted URL
        """
        pass

    @abstractmethod
    def _process_search_response(
        self, response: Response, query: str
    ) -> Generator[Publication, None, None]:
        """
        Process a search response.

        Args:
            response: HTTP response
            query: The original search query

        Returns:
            Generator of Publication objects

        Raises:
            DataProcessingError: If the response cannot be processed
        """
        pass

    @abstractmethod
    def _process_publication_response(
        self, response: Response, identifier: str
    ) -> Optional[Publication]:
        """
        Process a publication response.

        Args:
            response: HTTP response
            identifier: The publication identifier

        Returns:
            Publication object if found, otherwise None

        Raises:
            DataProcessingError: If the response cannot be processed
        """
        pass

    @staticmethod
    def get_nested_value(
        data: Dict[str, Any], key: str, nested_key: Optional[str] = None
    ) -> Any:
        """
        Safely extract a nested value from a dictionary.

        Args:
            data: Dictionary to extract from
            key: Primary key
            nested_key: Optional nested key

        Returns:
            Extracted value or None if not found
        """
        try:
            if nested_key is not None:
                if key in data and isinstance(data[key], dict):
                    return data[key].get(nested_key)
            else:
                return data.get(key)
        except (KeyError, TypeError, AttributeError):
            return None

        return None


class SemanticScholarScraper(WebScraper):
    """
    Scraper for the Semantic Scholar API.

    Extracts publication data from Semantic Scholar, which includes
    papers, authors, citations, and more.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        http_client: Optional[HttpClient] = None,
        rate_limit: float = 1.0,
    ):
        """
        Initialize the Semantic Scholar scraper.

        Args:
            base_url: Base URL for the Semantic Scholar API
            api_key: Optional API key for authenticated requests
            http_client: Optional HTTP client
            rate_limit: Minimum time between requests in seconds
        """
        super().__init__(
            base_url=base_url
            or "https://api.semanticscholar.org/graph/v1/paper/",
            http_client=http_client,
            rate_limit=rate_limit,
        )
        self.api_key = api_key

        # Add API key to headers if provided
        if api_key and self.http_client:
            self.http_client.session.headers.update({"x-api-key": api_key})

    def _format_search_url(self, query: str) -> str:
        """
        Format the URL for a Semantic Scholar search request.

        Args:
            query: Search query

        Returns:
            Formatted URL
        """
        # Default fields to retrieve
        fields = (
            "url,paperId,year,authors,externalIds,title,publicationDate,"
            "abstract,citationCount,journal,fieldsOfStudy,citations,references"
        )

        return f"search/match?query={quote_plus(query)}&fields={fields}"

    def _format_publication_url(self, identifier: str) -> str:
        """
        Format the URL for a Semantic Scholar publication request.

        Args:
            identifier: Publication identifier (DOI, Semantic Scholar ID, etc.)

        Returns:
            Formatted URL
        """
        # Check if the identifier is a DOI
        if identifier.startswith("10."):
            identifier = f"DOI:{identifier}"

        # Default fields to retrieve
        fields = (
            "url,paperId,year,authors,externalIds,title,publicationDate,"
            "abstract,citationCount,journal,fieldsOfStudy,citations,references"
        )

        return f"{identifier}?fields={fields}"

    def _process_search_response(
        self, response: Response, query: str
    ) -> Generator[Publication, None, None]:
        """
        Process a Semantic Scholar search response.

        Args:
            response: HTTP response
            query: The original search query

        Returns:
            Generator of Publication objects

        Raises:
            DataProcessingError: If the response cannot be processed
        """
        try:
            data = response.json()

            # Check if data contains results
            if not data or "data" not in data or not data["data"]:
                logger.info(f"No results found for query: {query}")
                return

            # Process each paper in the results
            for paper_data in data["data"]:
                publication = self._parse_paper_data(paper_data)
                if publication:
                    yield publication

        except json.JSONDecodeError as e:
            raise DataProcessingError(
                f"Failed to parse JSON response: {e}"
            ) from e
        except Exception as e:
            raise DataProcessingError(
                f"Failed to process search response: {e}"
            ) from e

    def _process_publication_response(
        self, response: Response, identifier: str
    ) -> Optional[Publication]:
        """
        Process a Semantic Scholar publication response.

        Args:
            response: HTTP response
            identifier: The publication identifier

        Returns:
            Publication object if found, otherwise None

        Raises:
            DataProcessingError: If the response cannot be processed
        """
        try:
            paper_data = response.json()

            # Check if paper data is valid
            if not paper_data or "paperId" not in paper_data:
                logger.info(
                    f"No publication found for identifier: {identifier}"
                )
                return None

            return self._parse_paper_data(paper_data)

        except json.JSONDecodeError as e:
            raise DataProcessingError(
                f"Failed to parse JSON response: {e}"
            ) from e
        except Exception as e:
            raise DataProcessingError(
                f"Failed to process publication response: {e}"
            ) from e

    def _parse_paper_data(self, paper_data: Dict[str, Any]) -> Publication:
        """
        Parse paper data from Semantic Scholar into a Publication object.

        Args:
            paper_data: Paper data from Semantic Scholar

        Returns:
            Publication object
        """
        # Extract basic fields
        title = self.get_nested_value(paper_data, "title") or "Unknown Title"

        # Create a publication object
        publication = Publication(title=title)

        # Set publication details
        publication.publication_date = (
            self.get_nested_value(paper_data, "publicationDate") or ""
        )
        publication.doi = (
            self.get_nested_value(paper_data, "externalIds", "DOI") or ""
        )
        publication.internal_id = (
            self.get_nested_value(paper_data, "paperId") or ""
        )
        publication.abstract = (
            self.get_nested_value(paper_data, "abstract") or ""
        )
        publication.citations_count = (
            self.get_nested_value(paper_data, "citationCount") or 0
        )
        publication.journal = (
            self.get_nested_value(paper_data, "journal", "name") or ""
        )
        publication.url = self.get_nested_value(paper_data, "url") or ""

        # Extract authors
        authors_data = paper_data.get("authors", [])
        if authors_data:
            publication.authors = [
                Author(
                    name=author.get("name", "Unknown Author"),
                    id=author.get("authorId", ""),
                    affiliation=(
                        author.get("affiliations", [""])[0]
                        if author.get("affiliations")
                        else ""
                    ),
                )
                for author in authors_data
            ]

        # Extract citations
        citations_data = paper_data.get("citations", [])
        if citations_data:
            publication.citations = [
                citation.get("title", f"Citation {i}")
                for i, citation in enumerate(citations_data, 1)
            ]

        # Extract references
        references_data = paper_data.get("references", [])
        if references_data:
            publication.references = [
                reference.get("title", f"Reference {i}")
                for i, reference in enumerate(references_data, 1)
            ]

        # Extract keywords/fields of study
        fields_of_study = paper_data.get("fieldsOfStudy", [])
        if fields_of_study:
            publication.keywords = fields_of_study

        return publication


class OrcidScraper(WebScraper):
    """
    Scraper for the ORCID API.

    Extracts publication and author data from ORCID, which is a
    persistent digital identifier for researchers.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        http_client: Optional[HttpClient] = None,
        rate_limit: float = 1.0,
    ):
        """
        Initialize the ORCID scraper.

        Args:
            base_url: Base URL for the ORCID API
            http_client: Optional HTTP client
            rate_limit: Minimum time between requests in seconds
        """
        super().__init__(
            base_url=base_url or "https://pub.orcid.org/v3.0/",
            http_client=http_client,
            rate_limit=rate_limit,
        )
        self.namespace = {"es": "http://www.orcid.org/ns/expanded-search"}

    def _format_search_url(self, query: str) -> str:
        """
        Format the URL for an ORCID search request.

        Args:
            query: Search query (author name)

        Returns:
            Formatted URL
        """
        # Format query for ORCID's search syntax
        formatted_query = (
            '{!edismax qf="given-and-family-names^50.0 family-name^10.0 given-names^10.0 '
            'credit-name^10.0 other-names^5.0 text^1.0" pf="given-and-family-names^50.0" '
            'bq="current-institution-affiliation-name:[* TO *]^100.0 '
            'past-institution-affiliation-name:[* TO *]^70" mm=1}' + query
        )

        params = {"q": formatted_query, "start": "0", "rows": "1"}

        return f"expanded-search?{urlencode(params, quote_via=quote_plus)}"

    def _format_publication_url(self, identifier: str) -> str:
        """
        Format the URL for an ORCID publication request.

        Args:
            identifier: ORCID identifier

        Returns:
            Formatted URL
        """
        params = {
            "offset": "0",
            "sort": "date",
            "sortAsc": "false",
            "pageSize": "50",
        }

        return f"{identifier}/worksExtendedPage.json?{urlencode(params)}"

    def _process_search_response(
        self, response: Response, query: str
    ) -> Generator[Publication, None, None]:
        """
        Process an ORCID search response.

        Args:
            response: HTTP response
            query: The original search query

        Returns:
            Generator of Publication objects

        Raises:
            DataProcessingError: If the response cannot be processed
        """
        try:
            # Extract the ORCID ID from the XML response
            orcid_id = self._parse_orcid_from_xml(response.text)

            if not orcid_id:
                logger.info(f"No ORCID ID found for query: {query}")
                return

            # Get the works for this ORCID ID
            works_url = self._format_publication_url(orcid_id)
            works_response = self.http_client.get(works_url)

            # Process the works
            yield from self._parse_orcid_works(works_response.text)

        except Exception as e:
            raise DataProcessingError(
                f"Failed to process ORCID search response: {e}"
            ) from e

    def _process_publication_response(
        self, response: Response, identifier: str
    ) -> Optional[Publication]:
        """
        Process an ORCID publication response.

        Args:
            response: HTTP response
            identifier: The ORCID identifier

        Returns:
            Publication object if found, otherwise None

        Raises:
            DataProcessingError: If the response cannot be processed
        """
        try:
            # Parse the works
            publications = list(self._parse_orcid_works(response.text))

            # Return the first publication if any were found
            return publications[0] if publications else None

        except Exception as e:
            raise DataProcessingError(
                f"Failed to process ORCID publication response: {e}"
            ) from e

    def _parse_orcid_from_xml(self, xml_text: str) -> Optional[str]:
        """
        Parse an ORCID ID from an XML response.

        Args:
            xml_text: XML response text

        Returns:
            ORCID ID if found, otherwise None
        """
        try:
            root = ET.fromstring(xml_text)
            result = root.find(".//es:orcid-id", self.namespace)

            if result is not None and result.text:
                return result.text

            return None

        except ET.ParseError as e:
            raise DataProcessingError(f"Failed to parse ORCID XML: {e}") from e

    def _parse_orcid_works(
        self, json_text: str
    ) -> Generator[Publication, None, None]:
        """
        Parse works from an ORCID JSON response.

        Args:
            json_text: JSON response text

        Returns:
            Generator of Publication objects

        Raises:
            DataProcessingError: If the response cannot be processed
        """
        try:
            data = json.loads(json_text)

            # Check if there are any works
            if "groups" not in data or not data["groups"]:
                return

            # Process each work group
            for group in data["groups"]:
                if "works" not in group or not group["works"]:
                    continue

                # Process each work in the group
                for work in group["works"]:
                    publication = self._parse_orcid_work(work)
                    if publication:
                        yield publication

        except json.JSONDecodeError as e:
            raise DataProcessingError(
                f"Failed to parse ORCID JSON: {e}"
            ) from e

    def _parse_orcid_work(self, work: Dict[str, Any]) -> Optional[Publication]:
        """
        Parse a single work from ORCID into a Publication.

        Args:
            work: Work data from ORCID

        Returns:
            Publication object if valid, otherwise None
        """
        # Extract the title
        title_container = work.get("title", {})
        title = (
            title_container.get("value", "")
            if isinstance(title_container, dict)
            else ""
        )

        if not title:
            return None

        # Create a publication
        publication = Publication(title=title)

        # Extract publication date
        pub_date_container = work.get("publicationDate", {})
        if pub_date_container and isinstance(pub_date_container, dict):
            year = pub_date_container.get("year", {}).get("value", "")
            month = pub_date_container.get("month", {}).get("value", "")
            day = pub_date_container.get("day", {}).get("value", "")

            if year:
                date_parts = [year]
                if month:
                    date_parts.append(month)
                if day:
                    date_parts.append(day)

                publication.publication_date = "-".join(date_parts)

        # Extract DOI
        external_ids = work.get("workExternalIdentifiers", [])
        for ext_id in external_ids:
            if (
                isinstance(ext_id, dict)
                and ext_id.get("externalIdentifierType", {})
                .get("value", "")
                .lower()
                == "doi"
            ):
                doi_container = ext_id.get("externalIdentifierId", {})
                publication.doi = (
                    doi_container.get("value", "")
                    if isinstance(doi_container, dict)
                    else ""
                )
                break

        # Extract internal ID
        put_code = work.get("putCode", {})
        publication.internal_id = (
            put_code.get("value", "") if isinstance(put_code, dict) else ""
        )

        # Extract journal
        journal_title = work.get("journalTitle", {})
        publication.journal = (
            journal_title.get("value", "")
            if isinstance(journal_title, dict)
            else ""
        )

        # Extract authors
        contributors = work.get("contributorsGroupedByOrcid", [])
        for contributor in contributors:
            if isinstance(contributor, dict) and "creditName" in contributor:
                credit_name = contributor["creditName"]
                name = (
                    credit_name.get("content", "")
                    if isinstance(credit_name, dict)
                    else ""
                )

                if name:
                    publication.authors.append(Author(name=name))

        return publication


# Factory functions for creating scrapers


def create_semantic_scholar_scraper(
    api_key: Optional[str] = None, rate_limit: float = 1.0
) -> SemanticScholarScraper:
    """
    Create a Semantic Scholar scraper.

    Args:
        api_key: Optional API key for authenticated requests
        rate_limit: Minimum time between requests in seconds

    Returns:
        Configured SemanticScholarScraper
    """
    return SemanticScholarScraper(api_key=api_key, rate_limit=rate_limit)


def create_orcid_scraper(rate_limit: float = 1.0) -> OrcidScraper:
    """
    Create an ORCID scraper.

    Args:
        rate_limit: Minimum time between requests in seconds

    Returns:
        Configured OrcidScraper
    """
    return OrcidScraper(rate_limit=rate_limit)
