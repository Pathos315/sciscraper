"""
File download functionality for scientific papers and resources.

This module provides classes for downloading files from various sources,
handling different file types, and managing the download process.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Optional, Protocol, Union, cast
from urllib.parse import urljoin, urlparse

from src.config import FilePath, config
from src.exceptions import ExportError, NetworkError
from src.http_client import HttpClient, Response
from src.log import logger


class FileExporter(Protocol):
    """Protocol for file export operations."""

    def export(self, content: bytes, filename: FilePath) -> Path:
        """
        Export content to a file.

        Args:
            content: The file content as bytes
            filename: The target filename

        Returns:
            Path to the exported file

        Raises:
            ExportError: If export fails
        """
        ...


@dataclass
class DownloadResult:
    """Result of a download operation."""

    success: bool
    """Whether the download was successful."""

    downloader_name: str
    """Name of the downloader used."""

    file_path: Optional[Path] = None
    """Path to the downloaded file if successful."""

    error_message: str = ""
    """Error message if download failed."""

    content_type: str = ""
    """Content type of the downloaded file."""

    @classmethod
    def success_result(
        cls, downloader_name: str, file_path: Path, content_type: str = ""
    ) -> DownloadResult:
        """Create a successful download result."""
        return cls(
            success=True,
            downloader_name=downloader_name,
            file_path=file_path,
            content_type=content_type,
        )

    @classmethod
    def failure_result(
        cls, downloader_name: str, error_message: str
    ) -> DownloadResult:
        """Create a failed download result."""
        return cls(
            success=False,
            downloader_name=downloader_name,
            error_message=error_message,
        )


class DirectFileExporter:
    """Exports files to a specified directory."""

    def __init__(self, export_dir: FilePath = None):
        """
        Initialize with export directory.

        Args:
            export_dir: Directory where files will be saved (defaults to config)
        """
        self.export_dir = Path(export_dir or config.export_dir)

    def export(self, content: bytes, filename: FilePath) -> Path:
        """
        Export content to a file.

        Args:
            content: The file content as bytes
            filename: The target filename

        Returns:
            Path to the exported file

        Raises:
            ExportError: If export fails
        """
        try:
            # Ensure export directory exists
            self.export_dir.mkdir(parents=True, exist_ok=True)

            # Create full file path
            file_path = self.export_dir / Path(filename).name

            # Write content to file using a temporary file
            with NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = Path(temp_file.name)

            # Move temporary file to final location
            temp_file_path.replace(file_path)

            return file_path

        except Exception as e:
            raise ExportError(
                f"Failed to export file: {e}", export_path=str(file_path)
            ) from e


class LinkParser:
    """Handles parsing and cleaning of download links."""

    # Regular expression for cleaning links
    LINK_CLEANING_PATTERN = re.compile(
        r"(?P<marker>location\.href=\')(?P<sep>/+)?"
    )

    @classmethod
    def clean_link(cls, link: str, base_url: str) -> Optional[str]:
        """
        Clean and normalize a download link.

        Args:
            link: The raw link to clean
            base_url: The base URL to use for relative links

        Returns:
            Cleaned link or None if the link is invalid
        """
        if not link:
            return None

        # Extract parts using regex
        match = cls.LINK_CLEANING_PATTERN.match(link)
        if not match:
            return None

        # Get marker and separator from match
        marker = match.group("marker")
        separator = match.group("sep") or ""

        # Remove marker
        link = link.replace(marker, "", 1)

        # Handle different separator types
        if separator == "//":
            # Protocol-relative URL
            return link.replace(separator, "https://", 1)
        elif separator:
            # Relative URL
            return urljoin(base_url, link.replace(separator, "", 1))
        else:
            # Absolute URL
            return link

    @classmethod
    def extract_download_link(
        cls, html: str, selector: str, attr: str = "onclick"
    ) -> Optional[str]:
        """
        Extract a download link from HTML content.

        Args:
            html: The HTML content
            selector: CSS selector to find the element
            attr: Attribute containing the link

        Returns:
            Extracted link or None if not found
        """
        try:
            from selectolax.parser import HTMLParser

            parser = HTMLParser(html)
            element = parser.css_first(selector)

            if not element or attr not in element.attributes:
                return None

            return element.attributes[attr]

        except Exception as e:
            logger.warning(f"Failed to extract download link: {e}")
            return None


@dataclass
class BaseDownloader:
    """Base class for downloaders."""

    name: str
    http_client: HttpClient
    exporter: FileExporter

    def download(self, identifier: str) -> DownloadResult:
        """
        Download content identified by the provided identifier.

        Args:
            identifier: Identifier for the content to download

        Returns:
            DownloadResult with success/failure information
        """
        try:
            # Fetch content
            content, filename, content_type = self._fetch_content(identifier)

            # Export to file
            file_path = self.exporter.export(content, filename)

            # Return success result
            return DownloadResult.success_result(
                downloader_name=self.name,
                file_path=file_path,
                content_type=content_type,
            )

        except Exception as e:
            logger.error(f"Download failed ({self.name}): {e}")
            return DownloadResult.failure_result(
                downloader_name=self.name, error_message=str(e)
            )

    def _fetch_content(self, identifier: str) -> tuple[bytes, str, str]:
        """
        Fetch content for the given identifier.

        Must be implemented by subclasses.

        Args:
            identifier: Identifier for the content

        Returns:
            Tuple of (content, filename, content_type)

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement _fetch_content")


@dataclass
class PaperDownloader(BaseDownloader):
    """Downloads academic papers from a paper repository."""

    base_url: str = field(default_factory=lambda: config.downloader_url)
    download_selector: str = "#buttons button:nth-child(1)"

    def _fetch_content(self, identifier: str) -> tuple[bytes, str, str]:
        """
        Fetch paper content for the given identifier.

        Args:
            identifier: Paper identifier (e.g., DOI)

        Returns:
            Tuple of (content, filename, content_type)

        Raises:
            NetworkError: If paper cannot be fetched
        """
        try:
            # Format the paper identifier
            paper_id = self._format_identifier(identifier)

            # Create search payload
            payload = {"request": paper_id}

            # Request the paper page
            search_response = self.http_client.post(
                self.base_url, data=payload
            )

            # Extract download link
            download_link = LinkParser.extract_download_link(
                search_response.text, self.download_selector
            )

            if not download_link:
                raise NetworkError(f"No download link found for {paper_id}")

            # Clean and normalize the link
            clean_link = LinkParser.clean_link(download_link, self.base_url)

            if not clean_link:
                raise NetworkError(
                    f"Failed to parse download link for {paper_id}"
                )

            # Download the paper
            paper_response = self.http_client.get(clean_link, stream=True)

            # Generate filename
            today = date.today().strftime("%y%m%d")
            filename = f"{today}_{self._sanitize_filename(paper_id)}.pdf"

            # Get content type
            content_type = paper_response.headers.get("Content-Type", "")

            return paper_response.content, filename, content_type

        except Exception as e:
            if isinstance(e, NetworkError):
                raise
            raise NetworkError(
                f"Failed to download paper {identifier}: {e}"
            ) from e

    def _format_identifier(self, identifier: str) -> str:
        """Format the identifier for the paper repository."""
        # Remove whitespace and normalize
        return identifier.strip().replace(" ", "")

    def _sanitize_filename(self, filename: str) -> str:
        """Make the filename safe for file systems."""
        # Replace problematic characters
        return re.sub(r'[\\/*?:"<>|]', "_", filename)


@dataclass
class ImageDownloader(BaseDownloader):
    """Downloads scientific images from URLs."""

    def _fetch_content(self, image_url: str) -> tuple[bytes, str, str]:
        """
        Fetch image content from the given URL.

        Args:
            image_url: URL of the image

        Returns:
            Tuple of (content, filename, content_type)

        Raises:
            NetworkError: If image cannot be fetched
        """
        try:
            # Download the image
            response = self.http_client.get(image_url, stream=True)

            # Determine file extension from URL or content type
            extension = self._get_file_extension(image_url, response)

            # Generate a unique filename
            filename = self._generate_filename(extension)

            # Get content type
            content_type = response.headers.get("Content-Type", "")

            return response.content, filename, content_type

        except Exception as e:
            if isinstance(e, NetworkError):
                raise
            raise NetworkError(
                f"Failed to download image {image_url}: {e}"
            ) from e

    def _get_file_extension(self, url: str, response: Response) -> str:
        """
        Determine file extension from URL or content type.

        Args:
            url: The image URL
            response: The HTTP response

        Returns:
            File extension (e.g., 'jpg', 'png')
        """
        # Try to get extension from URL
        path = urlparse(url).path
        _, ext = path.rsplit(".", 1) if "." in path else (path, "")

        if ext:
            return ext

        # Try to get extension from content type
        content_type = response.headers.get("Content-Type", "")
        content_type_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/gif": "gif",
            "image/svg+xml": "svg",
            "image/tiff": "tiff",
            "image/webp": "webp",
        }

        return content_type_map.get(content_type, "img")

    def _generate_filename(self, extension: str) -> str:
        """
        Generate a unique filename for the image.

        Args:
            extension: File extension

        Returns:
            Unique filename
        """
        today = date.today().strftime("%y%m%d")
        random_id = random.randint(1000, 9999)
        return f"{today}_image_{random_id}.{extension}"


# Factory functions for creating downloaders


def create_paper_downloader(
    export_dir: Optional[FilePath] = None,
) -> PaperDownloader:
    """
    Create a paper downloader with default configuration.

    Args:
        export_dir: Optional custom export directory

    Returns:
        Configured PaperDownloader
    """
    http_client = HttpClient(
        base_url=config.downloader_url, timeout=10, max_retries=2
    )

    exporter = DirectFileExporter(export_dir or config.export_dir)

    return PaperDownloader(
        name="PaperDownloader", http_client=http_client, exporter=exporter
    )


def create_image_downloader(
    export_dir: Optional[FilePath] = None,
) -> ImageDownloader:
    """
    Create an image downloader with default configuration.

    Args:
        export_dir: Optional custom export directory

    Returns:
        Configured ImageDownloader
    """
    http_client = HttpClient(timeout=10, max_retries=2)
    exporter = DirectFileExporter(export_dir or config.export_dir)

    return ImageDownloader(
        name="ImageDownloader", http_client=http_client, exporter=exporter
    )
