"""
Document analysis and text extraction functionality.

This module provides classes and functions for extracting, analyzing, and
scoring text content from documents based on target and excluded words.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, cast

import pdfplumber

from src.exceptions import DocumentError
from src.log import logger


@dataclass
class WordMatch:
    """Result of matching a set of words against a text."""

    matched_words: List[Tuple[str, int]]
    """List of (word, frequency) tuples for matched words."""

    total_matches: int
    """Total number of matches found."""

    def get_top_matches(self, n: int = 3) -> List[Tuple[str, int]]:
        """Get the top N matches by frequency."""
        return self.matched_words[: min(n, len(self.matched_words))]


@dataclass
class DocumentAnalysisResult:
    """Result of analyzing a document for target and excluded words."""

    target_matches: WordMatch
    """Matches with target words."""

    excluded_matches: WordMatch
    """Matches with excluded words."""

    word_count: int
    """Total word count in the document."""

    relevance_score: float
    """Relevance score from 0.0 to 1.0."""

    document_id: str = ""
    """Identifier for the document (e.g., DOI, filename)."""

    parenthetical_phrases: List[str] = field(default_factory=list)
    """Parenthetical phrases extracted from the document."""


class TextExtractor:
    """Extracts text from various document formats."""

    @staticmethod
    def from_pdf(file_path: Union[str, Path]) -> str:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text as a string

        Raises:
            DocumentError: If text extraction fails
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                text_pages = [
                    page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                    for page in pdf.pages
                ]
            return " ".join(text_pages)
        except Exception as e:
            raise DocumentError(f"Failed to extract text from PDF: {e}")


class TextProcessor:
    """Processes and analyzes text content."""

    PARENTHETICAL_PATTERN = re.compile(r"\(.*?\=.*?\)")

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Split text into individual words.

        Args:
            text: The text to tokenize

        Returns:
            List of words
        """
        # Simple tokenization - split on whitespace and lowercase
        return text.strip().lower().split()

    @staticmethod
    def extract_parentheticals(text: str) -> List[str]:
        """
        Extract parenthetical expressions containing equals signs.

        Args:
            text: Text to search

        Returns:
            List of matching parenthetical expressions
        """
        return TextProcessor.PARENTHETICAL_PATTERN.findall(text)

    @classmethod
    def match_words(cls, text: List[str], word_set: Set[str]) -> WordMatch:
        """
        Find matching words between text and a word set.

        Args:
            text: List of words to analyze
            word_set: Set of words to match against

        Returns:
            WordMatch containing match information
        """
        # Count word frequencies for words in the word set
        matches = Counter(word for word in text if word in word_set)

        # Get the most common matches
        most_common = matches.most_common()

        # Calculate total matches
        total = sum(count for _, count in most_common)

        return WordMatch(matched_words=most_common, total_matches=total)


class RelevanceCalculator:
    """Calculates document relevance based on word matches."""

    @staticmethod
    def calculate_score(
        total_words: int,
        target_matches: int,
        excluded_matches: int,
        target_weight: float = 1.0,
        excluded_weight: float = -0.25,
        neutral_weight: float = 0.5,
    ) -> float:
        """
        Calculate a relevance score based on word matches.

        Args:
            total_words: Total number of words in the document
            target_matches: Number of matches with target words
            excluded_matches: Number of matches with excluded words
            target_weight: Weight for target word matches
            excluded_weight: Weight for excluded word matches (typically negative)
            neutral_weight: Weight for words that match neither

        Returns:
            A score between 0.0 and 1.0
        """
        # Handle edge cases
        if total_words <= 0 or target_matches < 0 or excluded_matches < 0:
            return 0.0

        if target_matches + excluded_matches > total_words:
            logger.warning("Match counts exceed total word count, adjusting")
            target_matches = min(target_matches, total_words)
            excluded_matches = min(
                excluded_matches, total_words - target_matches
            )

        # Calculate the number of neutral words
        neutral_words = total_words - target_matches - excluded_matches

        # Calculate the weighted score
        weighted_sum = (
            target_matches * target_weight
            + excluded_matches * excluded_weight
            + neutral_words * neutral_weight
        )

        # Normalize to a 0-1 range
        score = weighted_sum / total_words

        # Clamp to 0-1 range
        return max(0.0, min(1.0, score))


class DocumentAnalyzer:
    """
    Analyzes documents for relevance based on target and excluded words.
    """

    def __init__(
        self,
        target_words_file: Union[str, Path],
        excluded_words_file: Union[str, Path],
    ):
        """
        Initialize with target and excluded word files.

        Args:
            target_words_file: Path to file containing target words
            excluded_words_file: Path to file containing excluded words
        """
        self.target_words = self._load_word_set(target_words_file)
        self.excluded_words = self._load_word_set(excluded_words_file)
        self.text_extractor = TextExtractor()
        self.text_processor = TextProcessor()

    def _load_word_set(self, file_path: Union[str, Path]) -> Set[str]:
        """
        Load words from a file into a set.

        Args:
            file_path: Path to the word file

        Returns:
            Set of words from the file

        Raises:
            DocumentError: If the file cannot be read
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return {line.strip().lower() for line in f if line.strip()}
        except Exception as e:
            raise DocumentError(
                f"Failed to load word set from {file_path}: {e}"
            )

    def analyze_pdf(
        self, pdf_path: Union[str, Path]
    ) -> DocumentAnalysisResult:
        """
        Analyze a PDF document for relevance.

        Args:
            pdf_path: Path to the PDF

        Returns:
            Analysis result with relevance score

        Raises:
            DocumentError: If analysis fails
        """
        try:
            # Extract text from PDF
            text = TextExtractor.from_pdf(pdf_path)

            # Extract parentheticals
            parentheticals = TextProcessor.extract_parentheticals(text)

            # Get document identifier (filename for now)
            doc_id = Path(pdf_path).stem

            # Analyze the text content
            result = self.analyze_text(text)

            # Add document-specific information
            result.document_id = doc_id
            result.parenthetical_phrases = parentheticals

            return result

        except Exception as e:
            if not isinstance(e, DocumentError):
                e = DocumentError(f"Failed to analyze PDF {pdf_path}: {e}")
            raise e

    def analyze_text(self, text: str) -> DocumentAnalysisResult:
        """
        Analyze text content for relevance.

        Args:
            text: The text to analyze

        Returns:
            Analysis result with relevance score

        Raises:
            DocumentError: If analysis fails
        """
        try:
            # Tokenize the text
            tokens = TextProcessor.tokenize(text)

            # Get word count
            word_count = len(tokens)

            # Match with target and excluded words
            target_matches = TextProcessor.match_words(
                tokens, self.target_words
            )
            excluded_matches = TextProcessor.match_words(
                tokens, self.excluded_words
            )

            # Calculate relevance score
            score = RelevanceCalculator.calculate_score(
                total_words=word_count,
                target_matches=target_matches.total_matches,
                excluded_matches=excluded_matches.total_matches,
            )

            # Create and return the result
            return DocumentAnalysisResult(
                target_matches=target_matches,
                excluded_matches=excluded_matches,
                word_count=word_count,
                relevance_score=score,
            )

        except Exception as e:
            raise DocumentError(f"Failed to analyze text: {e}")


# Convenience functions for common operations


def analyze_document(
    pdf_path: Union[str, Path],
    target_words_file: Union[str, Path],
    excluded_words_file: Union[str, Path],
) -> Dict:
    """
    Analyze a document and return the results as a dictionary.

    Args:
        pdf_path: Path to the PDF file
        target_words_file: Path to file with target words
        excluded_words_file: Path to file with excluded words

    Returns:
        Dictionary with analysis results

    Raises:
        DocumentError: If analysis fails
    """
    analyzer = DocumentAnalyzer(target_words_file, excluded_words_file)
    result = analyzer.analyze_pdf(pdf_path)

    # Convert to dictionary for easy serialization
    return {
        "document_id": result.document_id,
        "word_count": result.word_count,
        "relevance_score": result.relevance_score,
        "target_matches": result.target_matches.total_matches,
        "excluded_matches": result.excluded_matches.total_matches,
        "top_target_words": result.target_matches.get_top_matches(3),
        "top_excluded_words": result.excluded_matches.get_top_matches(3),
        "parenthetical_phrases": result.parenthetical_phrases,
    }


def calculate_relevance(
    text: str, target_words: Set[str], excluded_words: Set[str]
) -> float:
    """
    Calculate relevance score for a text against word sets.

    This is a simplified function for quick relevance checking.

    Args:
        text: Text to analyze
        target_words: Set of target words
        excluded_words: Set of excluded words

    Returns:
        Relevance score from 0.0 to 1.0
    """
    tokens = TextProcessor.tokenize(text)
    target_matches = TextProcessor.match_words(tokens, target_words)
    excluded_matches = TextProcessor.match_words(tokens, excluded_words)

    return RelevanceCalculator.calculate_score(
        total_words=len(tokens),
        target_matches=target_matches.total_matches,
        excluded_matches=excluded_matches.total_matches,
    )
