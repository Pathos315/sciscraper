"""
Data fetching and processing operations for scientific papers.

This module provides functions and classes for fetching data from various
sources, processing it, and returning structured results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, List, Optional, Protocol, TypeVar

import pandas as pd
from tqdm import tqdm

from src.config import FilePath, config
from src.log import logger

# Define type aliases for clarity
T = TypeVar("T")
DataFrame = pd.DataFrame


# Define protocols for better type checking
class DataSource(Protocol):
    """Protocol for any data source that can extract information from a given input."""

    def extract(self, input_data: Any) -> Any:
        """Extract data from the input source."""
        ...


class DataProcessor(Protocol):
    """Protocol for any data processor that can transform extracted data."""

    def process(self, data: Any) -> DataFrame:
        """Process extracted data into a DataFrame."""
        ...


@dataclass
class Fetcher:
    """
    Fetches and processes data from a source.

    This class combines a data source and optional processor to fetch
    and transform data into a structured format.
    """

    source: DataSource
    processor: Optional[Callable[[Any], DataFrame]] = None
    progress_bar: bool = True

    def fetch(self, input_data: Any) -> DataFrame:
        """
        Fetch data from the source and process it.

        Args:
            input_data: The input to pass to the data source

        Returns:
            A DataFrame containing the processed data
        """
        # Extract raw data from source
        raw_data = self._extract_with_progress(input_data)

        # Process the data if a processor is provided
        if self.processor:
            return self.processor(raw_data)

        # Otherwise, try to convert the raw data to a DataFrame
        if isinstance(raw_data, pd.DataFrame):
            return raw_data
        elif isinstance(raw_data, list):
            return pd.DataFrame(raw_data)
        else:
            raise ValueError(
                f"Cannot convert {type(raw_data)} to DataFrame without a processor"
            )

    def _extract_with_progress(self, input_data: Any) -> Any:
        """Extract data with an optional progress bar."""
        if not self.progress_bar:
            return self.source.extract(input_data)

        # If input_data is iterable, show progress for each item
        if isinstance(input_data, (list, tuple)):
            results = []
            for item in tqdm(input_data, desc="Extracting data", unit="items"):
                result = self.source.extract(item)
                if result is not None:
                    results.append(result)
            return results

        # Otherwise just extract the data directly
        return self.source.extract(input_data)


@dataclass
class Pipeline:
    """
    A data processing pipeline that can chain multiple operations.

    This class manages the end-to-end process of fetching, transforming,
    and exporting scientific paper data.
    """

    fetcher: Fetcher
    transformers: List[Callable[[DataFrame], DataFrame]] = field(
        default_factory=list
    )
    export_enabled: bool = True
    export_dir: FilePath = field(
        default_factory=lambda: Path(config.export_dir)
    )

    def process(self, input_data: Any) -> DataFrame:
        """
        Process input data through the entire pipeline.

        Args:
            input_data: The input to process

        Returns:
            The processed DataFrame
        """
        # Fetch the initial data
        df = self.fetcher.fetch(input_data)

        # Apply all transformers in sequence
        for transformer in self.transformers:
            df = transformer(df)

        # Export the result if enabled
        if self.export_enabled:
            self.export(df)

        return df

    def export(self, df: DataFrame, filename: Optional[str] = None) -> Path:
        """
        Export a DataFrame to CSV.

        Args:
            df: The DataFrame to export
            filename: Optional custom filename

        Returns:
            The path to the exported file
        """
        # Create export directory if it doesn't exist
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if not filename:
            today = date.today().strftime("%y%m%d")
            filename = f"{today}_sciscraper.csv"

        # Full path to the export file
        export_path = Path(self.export_dir) / filename

        # Rotate existing files
        self._rotate_files(export_path)

        # Export the DataFrame
        df.to_csv(export_path, index=False)
        logger.info(f"Exported data to {export_path}")

        return export_path

    def _rotate_files(self, export_path: Path, max_backups: int = 3) -> None:
        """Rotate existing files to maintain backup versions."""
        if not export_path.exists():
            return

        # Rotate existing backups
        for i in range(max_backups - 1, 0, -1):
            old_path = export_path.with_suffix(f".{i}.csv")
            new_path = export_path.with_suffix(f".{i+1}.csv")

            if old_path.exists():
                old_path.rename(new_path)

        # Rename the current file to .1.csv
        export_path.rename(export_path.with_suffix(".1.csv"))


# Standard transformers that can be used in pipelines
def remove_empty_columns(df: DataFrame) -> DataFrame:
    """Remove columns that contain only empty values."""
    return df.replace("", pd.NA).dropna(how="all", axis=1)


def optimize_dtypes(df: DataFrame) -> DataFrame:
    """Optimize data types in the DataFrame to reduce memory usage."""
    # Convert dates
    if "pub_date" in df.columns:
        df["pub_date"] = pd.to_datetime(df["pub_date"], errors="coerce")

    # Apply type conversions from config
    from src.config import KEY_TYPE_PAIRINGS

    for column, dtype in KEY_TYPE_PAIRINGS.items():
        if column in df.columns:
            try:
                df[column] = df[column].astype(dtype)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert column {column} to {dtype}")

    return df


# Factory functions to create common pipeline configurations
def create_document_pipeline(
    source: DataSource, export: bool = True
) -> Pipeline:
    """Create a pipeline for processing document data."""
    fetcher = Fetcher(source)

    return Pipeline(
        fetcher=fetcher,
        transformers=[
            remove_empty_columns,
            optimize_dtypes,
        ],
        export_enabled=export,
    )


def create_web_pipeline(source: DataSource, export: bool = True) -> Pipeline:
    """Create a pipeline for processing web data."""
    fetcher = Fetcher(source)

    return Pipeline(
        fetcher=fetcher,
        transformers=[
            remove_empty_columns,
            optimize_dtypes,
        ],
        export_enabled=export,
    )
