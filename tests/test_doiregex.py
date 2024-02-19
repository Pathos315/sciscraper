import pytest
from src.doi_regex import extract_identifier


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("10.1234/abc.123", "10.1234/abc.123"),
        ("10.1234/abc123", "10.1234/abc123"),
        ("https://doi.org/10.1234/abc.123", "10.1234/abc.123"),
        ("https://doi.org/10.1234/abc123", "10.1234/abc123"),
        ("https://doi.org/10.1234/123.456", "10.1234/123.456"),
        ("https://doi.org/10.1234/123456", "10.1234/123456"),
        ("1234.5678", "1234.5678"),
    ],
)
def test_extract_identifier(identifier, expected):
    assert extract_identifier(identifier) == expected
