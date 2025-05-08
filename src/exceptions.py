"""
Custom exceptions for the sciscraper package.

This module defines exception classes to represent various error conditions
that may occur throughout the application. These exceptions provide more
specific error information than standard Python exceptions.
"""

from __future__ import annotations

from typing import Any, Optional


class SciScraperError(Exception):
    """Base exception for all sciscraper errors."""

    def __init__(
        self, message: str, inner_exception: Optional[Exception] = None
    ):
        """
        Initialize with error message and optional inner exception.

        Args:
            message: The error message
            inner_exception: Optional original exception that caused this error
        """
        self.inner_exception = inner_exception
        if inner_exception:
            message = f"{message} (Caused by: {type(inner_exception).__name__}: {inner_exception})"
        super().__init__(message)


class ConfigurationError(SciScraperError):
    """Error related to configuration issues."""

    pass


class NetworkError(SciScraperError):
    """Error related to network or API operations."""

    pass


class DocumentError(SciScraperError):
    """Error related to document processing or analysis."""

    def __init__(
        self,
        message: str,
        document_path: Optional[str] = None,
        inner_exception: Optional[Exception] = None,
    ):
        """
        Initialize with error message, optional document path, and optional inner exception.

        Args:
            message: The error message
            document_path: Optional path to the document that caused the error
            inner_exception: Optional original exception that caused this error
        """
        self.document_path = document_path
        if document_path:
            message = f"{message} (Document: {document_path})"
        super().__init__(message, inner_exception)


class ExtractionError(SciScraperError):
    """Error related to data extraction operations."""

    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        inner_exception: Optional[Exception] = None,
    ):
        """
        Initialize with error message, optional source information, and optional inner exception.

        Args:
            message: The error message
            source: Optional source identifier (e.g., file path, URL)
            inner_exception: Optional original exception that caused this error
        """
        self.source = source
        if source:
            message = f"{message} (Source: {source})"
        super().__init__(message, inner_exception)


class ValidationError(SciScraperError):
    """Error related to data validation."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        inner_exception: Optional[Exception] = None,
    ):
        """
        Initialize with error message, optional field/value information, and optional inner exception.

        Args:
            message: The error message
            field: Optional name of the field that failed validation
            value: Optional invalid value
            inner_exception: Optional original exception that caused this error
        """
        self.field = field
        self.value = value
        if field:
            message = f"{message} (Field: {field}"
            if value is not None:
                message += f", Value: {value}"
            message += ")"
        super().__init__(message, inner_exception)


class DataProcessingError(SciScraperError):
    """Error related to data processing or transformation."""

    pass


class ExportError(SciScraperError):
    """Error related to data export operations."""

    def __init__(
        self,
        message: str,
        export_path: Optional[str] = None,
        inner_exception: Optional[Exception] = None,
    ):
        """
        Initialize with error message, optional export path, and optional inner exception.

        Args:
            message: The error message
            export_path: Optional path where export was attempted
            inner_exception: Optional original exception that caused this error
        """
        self.export_path = export_path
        if export_path:
            message = f"{message} (Path: {export_path})"
        super().__init__(message, inner_exception)


# Helper functions for creating exceptions with common patterns


def from_exception(
    exception_type: type[SciScraperError],
    original: Exception,
    message: Optional[str] = None,
) -> SciScraperError:
    """
    Create a custom exception from an original exception.

    Args:
        exception_type: The type of exception to create
        original: The original exception
        message: Optional custom message (if None, uses str(original))

    Returns:
        A new exception of the specified type
    """
    if message is None:
        message = str(original)
    return exception_type(message, inner_exception=original)


def document_error(
    message: str,
    document_path: Optional[str] = None,
    inner: Optional[Exception] = None,
) -> DocumentError:
    """
    Create a DocumentError with the specified parameters.

    Args:
        message: Error message
        document_path: Optional path to the document
        inner: Optional inner exception

    Returns:
        A new DocumentError
    """
    return DocumentError(message, document_path, inner)
