"""
Identifier extraction from PDF documents.

This module provides functionality to extract and validate document identifiers
(DOI, arXiv) from PDF files using various methods including metadata analysis,
text extraction, and external services.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Union,
    cast,
)

import pdfplumber

from src.doi_regex import extract_identifier
from src.exceptions import DocumentError
from src.http_client import HttpClient
from src.log import logger


class IdentifierType(Enum):
    """Types of document identifiers."""

    DOI = auto()
    ARXIV = auto()
    UNKNOWN = auto()

    @classmethod
    def from_string(cls, value: str) -> "IdentifierType":
        """Convert a string to an IdentifierType."""
        value = value.lower()
        if value in ("doi", "digital object identifier"):
            return cls.DOI
        elif value in ("arxiv", "arxivid", "arxiv id"):
            return cls.ARXIV
        return cls.UNKNOWN


@dataclass
class IdentifierResult:
    """Result of an identifier extraction operation."""

    identifier: str
    """The extracted identifier value."""

    id_type: IdentifierType
    """The type of the identifier."""

    method: str
    """Method used to extract the identifier."""

    confidence: float = 1.0
    """Confidence level (0.0-1.0) in the correctness of the identifier."""

    validated: bool = False
    """Whether the identifier has been validated."""

    source: str = ""
    """Source of the identifier (e.g., metadata field name)."""

    @property
    def is_valid(self) -> bool:
        """Check if this is a valid, high-confidence result."""
        return bool(
            self.identifier
            and self.confidence > 0.5
            and self.id_type != IdentifierType.UNKNOWN
        )

    @classmethod
    def create_doi_result(
        cls,
        doi: str,
        method: str,
        confidence: float = 1.0,
        validated: bool = False,
        source: str = "",
    ) -> "IdentifierResult":
        """Create a DOI result."""
        return cls(
            identifier=doi,
            id_type=IdentifierType.DOI,
            method=method,
            confidence=confidence,
            validated=validated,
            source=source,
        )

    @classmethod
    def create_arxiv_result(
        cls,
        arxiv_id: str,
        method: str,
        confidence: float = 1.0,
        validated: bool = False,
        source: str = "",
    ) -> "IdentifierResult":
        """Create an arXiv result."""
        return cls(
            identifier=arxiv_id,
            id_type=IdentifierType.ARXIV,
            method=method,
            confidence=confidence,
            validated=validated,
            source=source,
        )


class IdentifierExtractor:
    """
    Extracts document identifiers (DOI, arXiv) from PDFs.

    This class uses multiple extraction strategies, trying them in sequence
    until a valid identifier is found.
    """

    def __init__(self, http_client: Optional[HttpClient] = None):
        """
        Initialize the extractor.

        Args:
            http_client: Optional HTTP client for validation and online services
        """
        self.http_client = http_client or HttpClient()

    def extract_from_pdf(
        self, pdf_path: Union[str, Path], validate: bool = True
    ) -> Optional[IdentifierResult]:
        """
        Extract an identifier from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            validate: Whether to validate extracted identifiers

        Returns:
            IdentifierResult if an identifier was found, otherwise None

        Raises:
            DocumentError: If the PDF cannot be processed
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise DocumentError(f"PDF file not found: {pdf_path}")

            # Extract the metadata
            metadata = self._extract_metadata(pdf_path)

            # Try different extraction methods in sequence
            result = (
                # Method 1: Look in metadata for direct identifier fields
                self._find_in_metadata_fields(metadata)
                or
                # Method 2: Look for identifiers in PDF info dictionary text
                self._find_in_pdf_info(metadata)
                or
                # Method 3: Extract text from the first few pages and search
                self._find_in_pdf_text(pdf_path)
                or
                # Method 4: Try using the filename or title
                self._find_from_filename(pdf_path)
            )

            # Validate the result if requested
            if result and validate:
                self._validate_result(result)

            return result

        except Exception as e:
            if not isinstance(e, DocumentError):
                e = DocumentError(
                    f"Failed to extract identifier from PDF: {e}",
                    document_path=str(pdf_path),
                )
            logger.error(str(e))
            return None

    def _extract_metadata(self, pdf_path: Path) -> Dict:
        """
        Extract metadata from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary of metadata fields

        Raises:
            DocumentError: If metadata extraction fails
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata = pdf.metadata or {}
                logger.debug(f"Extracted metadata: {metadata}")
                return metadata
        except Exception as e:
            raise DocumentError(
                f"Failed to extract metadata: {e}", document_path=str(pdf_path)
            ) from e

    def _find_in_metadata_fields(
        self, metadata: Dict
    ) -> Optional[IdentifierResult]:
        """
        Look for identifiers in common metadata fields.

        Args:
            metadata: PDF metadata dictionary

        Returns:
            IdentifierResult if found, otherwise None
        """
        # Priority fields for DOI
        doi_fields = ["doi", "DOI", "Doi", "pdf2doi_identifier"]

        # Priority fields for arXiv
        arxiv_fields = ["arxiv", "arXiv", "ARXIV", "eprint"]

        # Check DOI fields
        for field in doi_fields:
            if field in metadata and metadata[field]:
                value = str(metadata[field]).strip()
                doi = extract_identifier(value)
                if doi:
                    logger.info(
                        f"Found DOI in metadata field '{field}': {doi}"
                    )
                    return IdentifierResult.create_doi_result(
                        doi=doi,
                        method="metadata_field",
                        confidence=0.9,
                        source=field,
                    )

        # Check arXiv fields
        for field in arxiv_fields:
            if field in metadata and metadata[field]:
                value = str(metadata[field]).strip()
                arxiv_id = extract_identifier(value)
                if arxiv_id:
                    logger.info(
                        f"Found arXiv ID in metadata field '{field}': {arxiv_id}"
                    )
                    return IdentifierResult.create_arxiv_result(
                        arxiv_id=arxiv_id,
                        method="metadata_field",
                        confidence=0.9,
                        source=field,
                    )

        return None

    def _find_in_pdf_info(self, metadata: Dict) -> Optional[IdentifierResult]:
        """
        Search for identifiers in the text of metadata fields.

        Args:
            metadata: PDF metadata dictionary

        Returns:
            IdentifierResult if found, otherwise None
        """
        # Skip fields that are already checked in metadata_fields
        skip_fields = {
            "doi",
            "DOI",
            "Doi",
            "arxiv",
            "arXiv",
            "ARXIV",
            "eprint",
        }

        # Check all metadata values
        for field, value in metadata.items():
            if field in skip_fields:
                continue

            if not value or not isinstance(value, str):
                continue

            # Try to find a DOI
            doi = extract_identifier(value)
            if doi:
                logger.info(f"Found DOI in metadata value '{field}': {doi}")
                return IdentifierResult.create_doi_result(
                    doi=doi,
                    method="metadata_text",
                    confidence=0.8,
                    source=field,
                )

            # Try to find an arXiv ID
            arxiv_id = extract_identifier(value)
            if arxiv_id:
                logger.info(
                    f"Found arXiv ID in metadata value '{field}': {arxiv_id}"
                )
                return IdentifierResult.create_arxiv_result(
                    arxiv_id=arxiv_id,
                    method="metadata_text",
                    confidence=0.8,
                    source=field,
                )

        return None

    def _find_in_pdf_text(self, pdf_path: Path) -> Optional[IdentifierResult]:
        """
        Extract text from PDF and search for identifiers.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            IdentifierResult if found, otherwise None
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Only process first few pages for efficiency
                max_pages = min(5, len(pdf.pages))

                # Extract text from each page
                for i in range(max_pages):
                    page = pdf.pages[i]
                    text = page.extract_text()

                    if not text:
                        continue

                    # Try to find a DOI
                    doi = extract_identifier(text)
                    if doi:
                        logger.info(
                            f"Found DOI in PDF text (page {i+1}): {doi}"
                        )
                        return IdentifierResult.create_doi_result(
                            doi=doi,
                            method="pdf_text",
                            confidence=0.7,
                            source=f"page_{i+1}",
                        )

                    # Try to find an arXiv ID
                    arxiv_id = extract_identifier(text)
                    if arxiv_id:
                        logger.info(
                            f"Found arXiv ID in PDF text (page {i+1}): {arxiv_id}"
                        )
                        return IdentifierResult.create_arxiv_result(
                            arxiv_id=arxiv_id,
                            method="pdf_text",
                            confidence=0.7,
                            source=f"page_{i+1}",
                        )

            return None

        except Exception as e:
            logger.warning(f"Failed to extract text from PDF: {e}")
            return None

    def _find_from_filename(
        self, pdf_path: Path
    ) -> Optional[IdentifierResult]:
        """
        Try to find an identifier in the filename.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            IdentifierResult if found, otherwise None
        """
        filename = pdf_path.stem

        # Try to find a DOI
        doi = extract_identifier(filename)
        if doi:
            logger.info(f"Found DOI in filename: {doi}")
            return IdentifierResult.create_doi_result(
                doi=doi, method="filename", confidence=0.6, source="filename"
            )

        # Try to find an arXiv ID
        arxiv_id = extract_identifier(filename)
        if arxiv_id:
            logger.info(f"Found arXiv ID in filename: {arxiv_id}")
            return IdentifierResult.create_arxiv_result(
                arxiv_id=arxiv_id,
                method="filename",
                confidence=0.6,
                source="filename",
            )

        return None

    def _validate_result(self, result: IdentifierResult) -> None:
        """
        Validate an identifier using appropriate web services.

        Args:
            result: The identifier result to validate

        Updates:
            The result's validated flag based on validation outcome
        """
        try:
            if result.id_type == IdentifierType.DOI:
                validated = self._validate_doi(result.identifier)
            elif result.id_type == IdentifierType.ARXIV:
                validated = self._validate_arxiv(result.identifier)
            else:
                validated = False

            result.validated = validated
            if validated:
                logger.info(
                    f"Validated {result.id_type.name}: {result.identifier}"
                )
            else:
                logger.warning(
                    f"Failed to validate {result.id_type.name}: {result.identifier}"
                )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            result.validated = False

    def _validate_doi(self, doi: str) -> bool:
        """
        Validate a DOI by checking with the DOI resolution service.

        Args:
            doi: The DOI to validate

        Returns:
            True if the DOI is valid, False otherwise
        """
        try:
            url = f"https://doi.org/api/handles/{doi}"
            response = self.http_client.get(url)

            if response.ok:
                data = response.json()
                return data.get("responseCode", 0) == 1

            return False

        except Exception as e:
            logger.warning(f"DOI validation failed: {e}")
            return False

    def _validate_arxiv(self, arxiv_id: str) -> bool:
        """
        Validate an arXiv ID by checking with the arXiv API.

        Args:
            arxiv_id: The arXiv ID to validate

        Returns:
            True if the arXiv ID is valid, False otherwise
        """
        try:
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = self.http_client.get(url)

            if response.ok:
                return "<entry>" in response.text

            return False

        except Exception as e:
            logger.warning(f"arXiv validation failed: {e}")
            return False


# Helper functions for common operations


def extract_doi_from_pdf(pdf_path: Union[str, Path]) -> Optional[str]:
    """
    Simple function to extract a DOI from a PDF.

    This is a convenience function for backward compatibility.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        DOI string if found, otherwise None
    """
    extractor = IdentifierExtractor()
    result = extractor.extract_from_pdf(pdf_path)

    if result and result.id_type == IdentifierType.DOI:
        return result.identifier

    return None


def extract_identifier_from_pdf(
    pdf_path: Union[str, Path], validate: bool = True
) -> Optional[IdentifierResult]:
    """
    Extract any identifier (DOI, arXiv) from a PDF.

    Args:
        pdf_path: Path to the PDF file
        validate: Whether to validate the identifier

    Returns:
        IdentifierResult if found, otherwise None
    """
    extractor = IdentifierExtractor()
    return extractor.extract_from_pdf(pdf_path, validate=validate)


class OnlineIdentifierService:
    """
    Service for finding document identifiers using online services.

    This service can search for identifiers using Google or other
    academic search engines.
    """

    def __init__(self, http_client: Optional[HttpClient] = None):
        """
        Initialize the service.

        Args:
            http_client: HTTP client for making requests
        """
        self.http_client = http_client or HttpClient()

    def search_by_title(
        self, title: str, max_results: int = 3
    ) -> Optional[IdentifierResult]:
        """
        Search for a document identifier using its title.

        Args:
            title: Document title
            max_results: Maximum number of search results to check

        Returns:
            IdentifierResult if found, otherwise None
        """
        try:
            # This would be implemented using a search API or web scraping
            # For now, we'll just log that this would happen
            logger.info(f"Would search for identifier using title: {title}")
            logger.info(
                "Online search functionality requires additional implementation"
            )

            # Mock implementation (in a real implementation, this would do a proper search)
            return None

        except Exception as e:
            logger.error(f"Failed to search by title: {e}")
            return None
