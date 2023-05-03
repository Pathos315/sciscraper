import re

regex_compile = re.compile

STANDARDIZED_DOI = regex_compile(
    r"(?xm)(?P<marker>doi[:\/\s]{0,3})?(?P<prefix>(?P<namespace> 10)[.](?P<registrant> \d{2,9}))(?P<sep>[:\-\/\s\]])(?P<suffix>[\-._;()\/:a-z0-9]+[a-z0-9])(?P<trailing> ([\s\n\"<.]|$))"
)

DOI_PATTERN_VERSION_0 = regex_compile(
    r"doi[\s\.\:]{0,2}(10\.\d{4}[\d\:\.\-\/a-z]+)(?:[\s\n\"<]|$)"
)
DOI_PATTERN_VERSION_1 = regex_compile(r"(10\.\d{4}[\d\:\.\-\/a-z]+)(?:[\s\n\"<]|$)")
DOI_PATTERN_VERSION_2 = regex_compile(
    r"(10\.\d{4}[\:\.\-\/a-z]+[\:\.\-\d]+)(?:[\s\na-z\"<]|$)"
)
DOI_PATTERN_VERSION_3 = regex_compile(
    r"https?://[ -~]*doi[ -~]*/(10\.\d{4,9}/[-._;()/:a-z0-9]+)(?:[\s\n\"<]|$)"
)
DOI_PATTERN_VERSION_4 = regex_compile(r"^(10\.\d{4,9}/[-._;()/:a-z0-9]+)$")
ARXIV_PATTERN_AFTER_2007 = regex_compile(r"^(\d{4}\.\d+)(?:v\d+)?$")
ARXIV_PATTERN_VERSION_0 = regex_compile(
    r"arxiv[\s]*\:[\s]*(\d{4}\.\d+)(?:v\d+)?(?:[\s\n\"<]|$)"
)
ARXIV_PATTERN_VERSION_1 = regex_compile(r"(\d{4}\.\d+)(?:v\d+)?(?:\.pdf)")
ARXIV_PATTERN_VERSION_2 = regex_compile(r"^(\d{4}\.\d+)(?:v\d+)?$")

IDENTIFIER_PATTERNS: dict[re.Pattern[str], str] = {
    DOI_PATTERN_VERSION_0: "doi",
    DOI_PATTERN_VERSION_1: "doi",
    DOI_PATTERN_VERSION_2: "doi",
    DOI_PATTERN_VERSION_3: "doi",
    DOI_PATTERN_VERSION_4: "doi",
    ARXIV_PATTERN_AFTER_2007: "arxiv",
    ARXIV_PATTERN_VERSION_0: "arxiv",
    ARXIV_PATTERN_VERSION_1: "arxiv",
    ARXIV_PATTERN_VERSION_2: "arxiv",
}


def standardize_doi(identifier: str) -> str | None:
    """
    Standardise a DOI by removing any marker, lowercase, and applying a consistent separator
    """
    match_dicts = ((match.groupdict()) for match in STANDARDIZED_DOI.finditer(identifier) if match)
    doi_meta = {key : match for key, match in match_dicts}
    return f"10.{doi_meta['registrant']}/{doi_meta['suffix']}" or None
