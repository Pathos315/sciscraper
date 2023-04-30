import re

STANDARDIZED_DOI = re.compile(r"(?xm)(?P<marker>doi[:\/\s]{0,3})?(?P<prefix>(?P<namespace> 10)[.](?P<registrant> \d{2,9}))(?P<sep>[:\-\/\s\]])(?P<suffix>[\-._;()\/:a-z0-9]+[a-z0-9])(?P<trailing> ([\s\n\"<.]|$))")

ARXIV_PATTERN_AFTER_2007 = re.compile(r'^(\d{4}\.\d+)(?:v\d+)?$')
DOI_PATTERN_VERSION_0 = re.compile(r'doi[\s\.\:]{0,2}(10\.\d{4}[\d\:\.\-\/a-z]+)(?:[\s\n\"<]|$)')
DOI_PATTERN_VERSION_1 = re.compile(r'(10\.\d{4}[\d\:\.\-\/a-z]+)(?:[\s\n\"<]|$)')
DOI_PATTERN_VERSION_2 = re.compile(r'(10\.\d{4}[\:\.\-\/a-z]+[\:\.\-\d]+)(?:[\s\na-z\"<]|$)')
DOI_PATTERN_VERSION_3 = re.compile(r'https?://[ -~]*doi[ -~]*/(10\.\d{4,9}/[-._;()/:a-z0-9]+)(?:[\s\n\"<]|$)')
DOI_PATTERN_VERSION_4 = re.compile(r'^(10\.\d{4,9}/[-._;()/:a-z0-9]+)$')
ARXIV_PATTERN_VERSION_0 = re.compile(r'arxiv[\s]*\:[\s]*(\d{4}\.\d+)(?:v\d+)?(?:[\s\n\"<]|$)')
ARXIV_PATTERN_VERSION_1 = re.compile(r'(\d{4}\.\d+)(?:v\d+)?(?:\.pdf)')
ARXIV_PATTERN_VERSION_2 = re.compile(r'^(\d{4}\.\d+)(?:v\d+)?$')

DOI_VERSIONS = [DOI_PATTERN_VERSION_0, DOI_PATTERN_VERSION_1, DOI_PATTERN_VERSION_2, DOI_PATTERN_VERSION_3, DOI_PATTERN_VERSION_4,]
ARXIV_VERSIONS = [ARXIV_PATTERN_VERSION_0, ARXIV_PATTERN_VERSION_1, ARXIV_PATTERN_VERSION_2,]

def standardize_doi(identifier):
    """
    Standardise a DOI by removing any marker, lowercase, and applying a consistent separator
    """
    doi_meta = dict()
    try:
        identifier: str = str(identifier[0]).lower() if isinstance(identifier, list) else identifier
    except IndexError:
        return None

    for match in STANDARDIZED_DOI.finditer(identifier):
        doi_meta.update(match.groupdict())

    if any(key not in doi_meta for key in ["registrant", "suffix"]):
        return None

    return f"10.{doi_meta['registrant']}/{doi_meta['suffix']}"


