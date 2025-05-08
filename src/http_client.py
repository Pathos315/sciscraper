"""
HTTP client functionality for making requests to external services.

This module provides a unified interface for making HTTP requests,
with consistent error handling and retry logic.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import requests
from requests import Response

from src.exceptions import NetworkError
from src.log import logger


@dataclass
class HttpClient:
    """
    HTTP client for making requests to external services.

    Features:
    - Automatic retries with exponential backoff
    - Consistent error handling
    - Base URL support
    - Request logging
    """

    base_url: str = ""
    timeout: int = 10
    max_retries: int = 3
    retry_backoff: float = 2.0
    session: Optional[requests.Session] = None

    def __post_init__(self) -> None:
        """Initialize the session if not provided."""
        if self.session is None:
            self.session = requests.Session()

    def get(self, url: str, **kwargs) -> Response:
        """
        Make a GET request.

        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            NetworkError: If the request fails
        """
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        """
        Make a POST request.

        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            NetworkError: If the request fails
        """
        return self._request("POST", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> Response:
        """
        Make an HTTP request with retries.

        Args:
            method: HTTP method (e.g., GET, POST)
            url: The URL to request
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            NetworkError: If the request fails
        """
        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        # Join with base URL if it's a relative URL
        if self.base_url and not url.startswith(("http://", "https://")):
            url = urljoin(self.base_url, url)

        # Try the request with retries
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    f"HTTP request: {method} {url} (attempt {attempt})"
                )

                response = self.session.request(method, url, **kwargs)

                if response.ok:
                    return response

                error_msg = f"HTTP error: {response.status_code} for {url}"
                last_error = NetworkError(error_msg)
                logger.warning(
                    f"{error_msg} (attempt {attempt}/{self.max_retries})"
                )

            except requests.RequestException as e:
                error_msg = f"Request failed: {e}"
                last_error = NetworkError(error_msg, inner_exception=e)
                logger.warning(
                    f"{error_msg} (attempt {attempt}/{self.max_retries})"
                )

            # Don't sleep on the last attempt
            if attempt < self.max_retries:
                # Exponential backoff
                sleep_time = self.retry_backoff ** (attempt - 1)
                time.sleep(sleep_time)

        # If we got here, all retries failed
        if last_error:
            raise last_error

        # This should never happen, but just in case
        raise NetworkError(f"All requests failed for {url}")
