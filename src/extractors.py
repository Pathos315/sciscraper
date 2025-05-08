"""
Data extraction utilities for various source types.

This module provides functions and classes for extracting data from files,
directories, DataFrames and other sources into consistent formats for further
processing.
"""

from __future__ import annotations

import os
from ast import literal_eval
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

import pandas as pd

from src.config import UTF, FilePath
from src.log import log_debug, logger

# Type variables for generic functions
T = TypeVar("T")
S = TypeVar("S")


class ExtractionError(Exception):
    """Exception raised when data extraction fails."""

    pass


@dataclass
class ExtractorResult(Generic[T]):
    """Container for extraction results with metadata."""

    data: T
    source: str
    success: bool = True
    error: Optional[str] = None

    @classmethod
    def success(cls, data: T, source: str) -> ExtractorResult[T]:
        """Create a successful result."""
        return cls(data=data, source=source, success=True)

    @classmethod
    def failure(cls, source: str, error: str) -> ExtractorResult[Any]:
        """Create a failed result."""
        return cls(data=None, source=source, success=False, error=error)


class Extractor(Generic[S, T]):
    """Base class for data extractors."""

    def extract(self, source: S) -> ExtractorResult[T]:
        """
        Extract data from the source.

        Args:
            source: The source to extract data from

        Returns:
            An ExtractorResult containing the extracted data or error information
        """
        try:
            result = self._do_extract(source)
            return ExtractorResult.success(result, str(source))
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractorResult.failure(str(source), str(e))

    def _do_extract(self, source: S) -> T:
        """
        Perform the actual extraction.

        This method should be implemented by subclasses.

        Args:
            source: The source to extract data from

        Returns:
            The extracted data

        Raises:
            ExtractionError: If extraction fails
        """
        raise NotImplementedError("Subclasses must implement _do_extract")


class TextFileExtractor(Extractor[FilePath, List[str]]):
    """Extracts data from text files as lists of words."""

    def __init__(self, lowercase: bool = True, strip: bool = True):
        self.lowercase = lowercase
        self.strip = strip

    def _do_extract(self, file_path: FilePath) -> List[str]:
        """Extract words from a text file."""
        try:
            with open(file_path, encoding=UTF) as file:
                words = []
                for line in file:
                    word = line
                    if self.strip:
                        word = word.strip()
                    if self.lowercase:
                        word = word.lower()
                    words.append(word)
                return words
        except (IOError, UnicodeDecodeError) as e:
            raise ExtractionError(f"Failed to read text file {file_path}: {e}")


class CsvColumnExtractor(Extractor[FilePath, List[str]]):
    """Extracts a specific column from a CSV file."""

    def __init__(self, column: str = "title", fill_na: str = "N/A"):
        self.column = column
        self.fill_na = fill_na

    def _do_extract(self, file_path: FilePath) -> List[str]:
        """Extract a column from a CSV file."""
        try:
            data = pd.read_csv(
                file_path, skip_blank_lines=True, usecols=[self.column]
            )

            # Handle missing values
            data = data.fillna(self.fill_na)

            # Extract the column as a list
            data_list = data[self.column].tolist()

            # Clean any nested columns (dictionaries or lists stored as strings)
            return self._clean_nested_values(data_list)

        except Exception as e:
            raise ExtractionError(f"Failed to extract column from CSV: {e}")

    def _clean_nested_values(self, data_list: List[str]) -> List[str]:
        """
        Clean nested values in the data list.

        Some CSV columns may contain serialized dictionaries or lists.
        This method attempts to parse them.

        Args:
            data_list: The list of values to clean

        Returns:
            The cleaned list with any nested values processed
        """
        result = []

        # Process regular strings
        for item in data_list:
            if not isinstance(item, str) or not item.startswith("{"):
                result.append(item)
                continue

            # Try to parse as a literal Python object
            try:
                parsed = literal_eval(item)
                # If the parsed result is a dictionary, try to extract the column
                if isinstance(parsed, dict) and self.column in parsed:
                    result.append(parsed[self.column])
                else:
                    result.append(parsed)
            except (ValueError, SyntaxError):
                # If parsing fails, keep the original string
                result.append(item)

        return result


class DirectoryExtractor(Extractor[FilePath, List[Path]]):
    """Extracts files with a specific suffix from a directory."""

    def __init__(self, suffix: str = "pdf", recursive: bool = True):
        self.suffix = suffix
        self.recursive = recursive

    def _do_extract(self, directory: FilePath) -> List[Path]:
        """Extract files from a directory."""
        try:
            path = Path(directory)
            if not path.is_dir():
                raise ExtractionError(f"{path} is not a directory")

            if self.recursive:
                return list(path.rglob(f"*.{self.suffix}"))
            else:
                return list(path.glob(f"*.{self.suffix}"))

        except Exception as e:
            raise ExtractionError(
                f"Failed to extract files from directory: {e}"
            )


class DataFrameColumnExtractor(Extractor[pd.DataFrame, List[Any]]):
    """Extracts a single column from a DataFrame."""

    def __init__(self, column: str = "title", fill_na: str = "N/A"):
        self.column = column
        self.fill_na = fill_na

    def _do_extract(self, df: pd.DataFrame) -> List[Any]:
        """Extract a column from a DataFrame."""
        try:
            if self.column not in df.columns:
                raise ExtractionError(
                    f"Column '{self.column}' not found in DataFrame"
                )

            # Make a copy to avoid modifying the original
            df_copy = df.copy()

            # Fill missing values and convert to list
            return df_copy[self.column].fillna(self.fill_na).tolist()

        except Exception as e:
            raise ExtractionError(
                f"Failed to extract column from DataFrame: {e}"
            )


class DataFrameReferenceExtractor(
    Extractor[pd.DataFrame, tuple[List[Any], List[Any]]]
):
    """
    Extracts two columns from a DataFrame, expanding list-like data.

    This extractor is useful for cases where one column contains lists of references
    that need to be expanded, while keeping track of the source in another column.
    """

    def __init__(
        self,
        value_column: str = "citations",
        reference_column: str = "title",
        fill_na: str = "N/A",
    ):
        self.value_column = value_column
        self.reference_column = reference_column
        self.fill_na = fill_na

    def _do_extract(self, df: pd.DataFrame) -> tuple[List[Any], List[Any]]:
        """
        Extract and expand list-like data from a DataFrame.

        Args:
            df: The DataFrame to extract from

        Returns:
            A tuple containing two lists:
            - The expanded values from value_column
            - The corresponding reference values from reference_column
        """
        try:
            # Verify columns exist
            for col in [self.value_column, self.reference_column]:
                if col not in df.columns:
                    raise ExtractionError(
                        f"Column '{col}' not found in DataFrame"
                    )

            # Make a copy and explode the list-like column
            df_copy = df.copy()

            # Handle potential errors in the explode operation
            try:
                exploded = df_copy.explode(self.value_column)
            except (ValueError, TypeError) as e:
                raise ExtractionError(
                    f"Failed to explode column '{self.value_column}': {e}"
                )

            # Extract both columns as lists, filling NA values
            values = exploded[self.value_column].fillna(self.fill_na).tolist()
            references = (
                exploded[self.reference_column].fillna(self.fill_na).tolist()
            )

            return values, references

        except Exception as e:
            if not isinstance(e, ExtractionError):
                e = ExtractionError(f"Failed to extract reference data: {e}")
            raise e


# Factory functions for common extraction scenarios
def create_text_extractor(lowercase: bool = True) -> TextFileExtractor:
    """Create a TextFileExtractor with common settings."""
    return TextFileExtractor(lowercase=lowercase, strip=True)


def create_csv_extractor(column: str) -> CsvColumnExtractor:
    """Create a CsvColumnExtractor for a specific column."""
    return CsvColumnExtractor(column=column)


def create_pdf_extractor() -> DirectoryExtractor:
    """Create a DirectoryExtractor configured for PDF files."""
    return DirectoryExtractor(suffix="pdf", recursive=True)


def create_dataframe_extractor(column: str) -> DataFrameColumnExtractor:
    """Create a DataFrameColumnExtractor for a specific column."""
    return DataFrameColumnExtractor(column=column)
