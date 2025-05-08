"""
Document identifier pattern matching and extraction.

This module provides functionality for extracting, validating, and normalizing
document identifiers (DOI, arXiv ID) from various text sources using regular
expressions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Pattern, Union


class IdentifierType(Enum):
    """Types of document identifiers that can be extracted."""

    DOI = "doi"
    ARXIV = "arxiv"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "IdentifierType":
        """Convert a string to an IdentifierType enum value."""
        value = value.lower()
        if value == "doi":
            return cls.DOI
        elif value == "arxiv":
            return cls.ARXIV
        return cls.UNKNOWN


@dataclass
class IdentifierMatch:
    """Result of an identifier matching operation."""

    value: str
    """The extracted identifier value."""

    id_type: IdentifierType
    """Type of the identifier (DOI, arXiv, etc.)."""

    original_text: str
    """The original text from which the identifier was extracted."""

    start_pos: int = 0
    """Starting position in the original text."""

    end_pos: int = 0
    """Ending position in the original text."""

    @property
    def is_valid(self) -> bool:
        """Check if this match contains a valid identifier."""
        return bool(self.value and self.id_type != IdentifierType.UNKNOWN)


# Regular expressions for DOI matching
# These are carefully constructed patterns for different DOI formats
DOI_PATTERNS = [
    # Pattern for DOIs with explicit "doi:" prefix
    re.compile(
        r"doi[\s\.\:]{0,2}(10\.\d{4}[\d\:\.\-\/a-z]+)(?:[\s\n\"<]|$)",
        re.IGNORECASE,
    ),
    # Pattern for bare DOIs starting with 10.
    re.compile(r"(10\.\d{4}[\d\:\.\-\/a-z]+)(?:[\s\n\"<]|$)"),
    # Pattern for DOIs with unusual formatting
    re.compile(r"(10\.\d{4}[\:\.\-\/a-z]+[\:\.\-\d]+)(?:[\s\na-z\"<]|$)"),
    # Pattern for DOIs in URLs
    re.compile(
        r"https?://[ -~]*doi[ -~]*/(10\.\d{4,9}/[-._;()/:a-z0-9]+)(?:[\s\n\"<]|$)",
        re.IGNORECASE,
    ),
    # Pattern for exact DOIs (whole string)
    re.compile(r"^(10\.\d{4,9}/[-._;()/:a-z0-9]+)$"),
]

# Detailed DOI pattern with named capture groups for components
DOI_REGEX = re.compile(
    r"""(?xm)
    (?P<marker>   doi[:\/\s]{0,3})?
    (?P<prefix>
        (?P<namespace> 10)
        [.]
        (?P<registrant> \d{2,9})
    )
    (?P<sep>     [:\-\/\s\]])
    (?P<suffix>  [\-._;()\/:a-z0-9]+[a-z0-9])
    (?P<trailing> ([\s\n\"<.]|$))
    """,
    re.IGNORECASE,
)

# Regular expressions for arXiv ID matching
ARXIV_PATTERNS = [
    # Pattern for bare arXiv IDs (YYMM.NNNNN format)
    re.compile(r"^(\d{4}\.\d+)(?:v\d+)?$"),
    # Pattern for arXiv IDs with prefix
    re.compile(
        r"arxiv[\s]*\:[\s]*(\d{4}\.\d+)(?:v\d+)?(?:[\s\n\"<]|$)", re.IGNORECASE
    ),
    # Pattern for arXiv IDs in filenames
    re.compile(r"(\d{4}\.\d+)(?:v\d+)?(?:\.pdf)"),
    # Pattern for exact arXiv IDs (whole string)
    re.compile(r"^(\d{4}\.\d+)(?:v\d+)?$"),
]

# Detailed arXiv pattern with named capture groups
ARXIV_REGEX = re.compile(
    r"""(?x)
    (?P<marker>arxiv[:\/\s]{0,3})?  # Marker (optional)
    (?P<identifier>\d{4}\.\d+)       # Identifier (mandatory)
    (?:v\d+)?                        # Version (optional)
    (?P<trailing>\.pdf)?$            # Trailing '.pdf' (optional)
    """,
    re.IGNORECASE,
)

# Map of identifier types to their pattern collections
IDENTIFIER_PATTERNS = {
    IdentifierType.DOI: DOI_PATTERNS,
    IdentifierType.ARXIV: ARXIV_PATTERNS,
}


class IdentifierExtractor:
    """Extracts document identifiers from text using regular expressions."""

    @classmethod
    def extract_identifier(
        cls, text: str, id_type: Optional[IdentifierType] = None
    ) -> Optional[IdentifierMatch]:
        """
        Extract an identifier from text.

        Args:
            text: Text to extract from
            id_type: Optional specific identifier type to extract

        Returns:
            IdentifierMatch if found, otherwise None
        """
        if not text:
            return None

        # Normalize text for better matching
        text_normalized = text.strip()

        # If id_type is specified, only check that type
        if id_type and id_type != IdentifierType.UNKNOWN:
            return cls._extract_specific_type(text_normalized, id_type)

        # Otherwise, try DOI first, then arXiv
        return cls._extract_specific_type(
            text_normalized, IdentifierType.DOI
        ) or cls._extract_specific_type(text_normalized, IdentifierType.ARXIV)

    @classmethod
    def extract_all_identifiers(cls, text: str) -> List[IdentifierMatch]:
        """
        Extract all identifiers from text.

        Args:
            text: Text to extract from

        Returns:
            List of all identified IdentifierMatch objects
        """
        results = []

        # Try to find DOIs
        doi_matches = cls._find_all_pattern_matches(text, IdentifierType.DOI)
        results.extend(doi_matches)

        # Try to find arXiv IDs
        arxiv_matches = cls._find_all_pattern_matches(
            text, IdentifierType.ARXIV
        )
        results.extend(arxiv_matches)

        return results

    @classmethod
    def _extract_specific_type(
        cls, text: str, id_type: IdentifierType
    ) -> Optional[IdentifierMatch]:
        """
        Extract a specific type of identifier from text.

        Args:
            text: Text to extract from
            id_type: Type of identifier to extract

        Returns:
            IdentifierMatch if found, otherwise None
        """
        patterns = IDENTIFIER_PATTERNS.get(id_type, [])

        for pattern in patterns:
            match = pattern.search(text)
            if match:
                # The first group contains the identifier
                raw_id = match.group(1)

                # Standardize the identifier
                standardized = cls.standardize_identifier(raw_id, id_type)

                if standardized:
                    return IdentifierMatch(
                        value=standardized,
                        id_type=id_type,
                        original_text=text,
                        start_pos=match.start(1),
                        end_pos=match.end(1),
                    )

        return None

    @classmethod
    def _find_all_pattern_matches(
        cls, text: str, id_type: IdentifierType
    ) -> List[IdentifierMatch]:
        """
        Find all matches of a specific identifier type in text.

        Args:
            text: Text to search in
            id_type: Type of identifier to find

        Returns:
            List of IdentifierMatch objects
        """
        results = []
        patterns = IDENTIFIER_PATTERNS.get(id_type, [])

        for pattern in patterns:
            for match in pattern.finditer(text):
                # The first group contains the identifier
                raw_id = match.group(1)

                # Standardize the identifier
                standardized = cls.standardize_identifier(raw_id, id_type)

                if standardized:
                    results.append(
                        IdentifierMatch(
                            value=standardized,
                            id_type=id_type,
                            original_text=text,
                            start_pos=match.start(1),
                            end_pos=match.end(1),
                        )
                    )

        return results

    @staticmethod
    def standardize_identifier(
        identifier: str, id_type: IdentifierType
    ) -> str:
        """
        Standardize an identifier by removing prefixes and normalizing format.

        Args:
            identifier: The identifier to standardize
            id_type: Type of the identifier

        Returns:
            Standardized identifier
        """
        if not identifier:
            return ""

        if id_type == IdentifierType.DOI:
            return IdentifierExtractor._standardize_doi(identifier)
        elif id_type == IdentifierType.ARXIV:
            return IdentifierExtractor._standardize_arxiv(identifier)

        return identifier

    @staticmethod
    def _standardize_doi(doi: str) -> str:
        """
        Standardize a DOI by removing prefixes and normalizing format.

        Args:
            doi: The DOI to standardize

        Returns:
            Standardized DOI
        """
        # Try to match the DOI components
        match = DOI_REGEX.search(doi.lower())
        if not match:
            return ""

        # Extract components
        meta = match.groupdict()

        # Format the DOI as 10.NNNN/SUFFIX
        if "registrant" in meta and "suffix" in meta:
            return f"10.{meta['registrant']}/{meta['suffix']}"

        return ""

    @staticmethod
    def _standardize_arxiv(arxiv_id: str) -> str:
        """
        Standardize an arXiv ID by removing prefixes and version numbers.

        Args:
            arxiv_id: The arXiv ID to standardize

        Returns:
            Standardized arXiv ID
        """
        # Try to match the arXiv ID components
        match = ARXIV_REGEX.search(arxiv_id.lower())
        if not match:
            return ""

        # Extract the core identifier (without version)
        meta = match.groupdict()
        if "identifier" in meta:
            return meta["identifier"]

        return ""


# Convenience functions for common operations


def extract_identifier(text: str) -> str:
    """
    Extract a document identifier (DOI or arXiv) from text.

    This is a convenience function that returns just the identifier string.

    Args:
        text: Text to extract from

    Returns:
        Identifier string if found, otherwise empty string
    """
    match = IdentifierExtractor.extract_identifier(text)
    return match.value if match else ""


def extract_doi(text: str) -> str:
    """
    Extract a DOI from text.

    Args:
        text: Text to extract from

    Returns:
        DOI string if found, otherwise empty string
    """
    match = IdentifierExtractor.extract_identifier(text, IdentifierType.DOI)
    return match.value if match else ""


def extract_arxiv(text: str) -> str:
    """
    Extract an arXiv ID from text.

    Args:
        text: Text to extract from

    Returns:
        arXiv ID string if found, otherwise empty string
    """
    match = IdentifierExtractor.extract_identifier(text, IdentifierType.ARXIV)
    return match.value if match else ""


def is_valid_doi(text: str) -> bool:
    """
    Check if the text contains a valid DOI.

    Args:
        text: Text to check

    Returns:
        True if the text contains a valid DOI, otherwise False
    """
    return bool(extract_doi(text))


def is_valid_arxiv(text: str) -> bool:
    """
    Check if the text contains a valid arXiv ID.

    Args:
        text: Text to check

    Returns:
        True if the text contains a valid arXiv ID, otherwise False
    """
    return bool(extract_arxiv(text))
