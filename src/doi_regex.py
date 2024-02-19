from __future__ import annotations

import re


STANDARDIZED_DOI = re.compile(
    r"(?xm)(?P<marker>doi[:\/\s]{0,3})?(?P<prefix>(?P<namespace> 10)[.](?P<registrant> \d{2,9}))(?P<sep>[:\-\/\s\]])(?P<suffix>[\-._;()\/:a-z0-9]+[a-z0-9])(?P<trailing> ([\s\n\"<.]|$))"
)

DOI_PATTERNS = [
    re.compile(r"doi[\s\.\:]{0,2}(10\.\d{4}[\d\:\.\-\/a-z]+)(?:[\s\n\"<]|$)"),
    re.compile(r"(10\.\d{4}[\d\:\.\-\/a-z]+)(?:[\s\n\"<]|$)"),
    re.compile(r"(10\.\d{4}[\:\.\-\/a-z]+[\:\.\-\d]+)(?:[\s\na-z\"<]|$)"),
    re.compile(
        r"https?://[ -~]*doi[ -~]*/(10\.\d{4,9}/[-._;()/:a-z0-9]+)(?:[\s\n\"<]|$)"
    ),
    re.compile(r"^(10\.\d{4,9}/[-._;()/:a-z0-9]+)$"),
]
ARXIV_PATTERNS = [
    re.compile(r"^(\d{4}\.\d+)(?:v\d+)?$"),
    re.compile(r"arxiv[\s]*\:[\s]*(\d{4}\.\d+)(?:v\d+)?(?:[\s\n\"<]|$)"),
    re.compile(r"(\d{4}\.\d+)(?:v\d+)?(?:\.pdf)"),
    re.compile(r"^(\d{4}\.\d+)(?:v\d+)?$"),
]


IDENTIFIER_TYPES: dict[str, list[re.Pattern[str]]] = {
    "doi": DOI_PATTERNS,
    "arxiv": ARXIV_PATTERNS,
}


def standardize_doi(identifier: str) -> str | None:  # type: ignore[return]
    """
    Standardise a DOI by removing any marker, lowercase, and applying a consistent separator
    """
    for identifier_type, patterns in IDENTIFIER_TYPES.items():
        for pattern in patterns:
            match = pattern.search(identifier)
            if not match:
                return None
            if identifier_type == "doi":
                return f"10.{match.group(1)}"
            elif identifier_type == "arxiv":
                return match.group(1)
