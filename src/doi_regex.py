from __future__ import annotations
from itertools import chain
import re

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
"""
)

ARXIV_REGEX = re.compile(r"^(\d{4}\.\d+)(?:v\d+)?(?:\.pdf)?$")

IDENTIFIER_PATTERNS = {"doi": DOI_PATTERNS, "arxiv": ARXIV_PATTERNS}


def extract_identifier(
    text: str,
) -> str | None:
    """Extract doi or arXiv identifier from a string"""
    pattern_list = chain.from_iterable(IDENTIFIER_PATTERNS.values())
    for pattern in pattern_list:
        if match := pattern.search(text.casefold()):
            return match.group(0)
    return None
