"""
Factory functions for creating data processors and scrapers.

This module provides factory functions to create configured instances of
various scrapers, processors, and pipelines for different use cases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Union

from src.config import config
from src.docscraper import DocumentAnalyzer
from src.doifrompdf import IdentifierExtractor
from src.downloaders import create_image_downloader, create_paper_downloader
from src.extractors import CsvColumnExtractor, DirectoryExtractor
from src.fetch import Fetcher, Pipeline, optimize_dtypes, remove_empty_columns
from src.log import logger
from src.webscrapers import (
    create_orcid_scraper,
    create_semantic_scholar_scraper,
)


class SciScraper:
    """
    Main scraper class for scientific papers.

    This class provides a unified interface for various scraping operations,
    handling initialization, logging, processing, and export.
    """

    def __init__(
        self,
        pipeline: Pipeline,
        debug: bool = True,
        export: bool = True,
    ):
        """
        Initialize the scraper.

        Args:
            pipeline: Data processing pipeline
            debug: Whether to enable debug logging
            export: Whether to export results
        """
        self.pipeline = pipeline
        self.debug = debug
        self.export = export
        self.logger = logger

    def __call__(self, input_path: Union[str, Path]) -> None:
        """
        Run the scraper on the input path.

        Args:
            input_path: Path to the input file or directory
        """
        self.set_logging()

        logger.info(
            "Debug logging status: '%s'\n"
            "Commencing sciscrape on file: '%s'...\n",
            self.debug,
            input_path,
        )

        # Process the input through the pipeline
        result = self.pipeline.process(input_path)

        # Log the results
        logger.info(f"Processing complete: {len(result)} records found")

    def set_logging(self) -> None:
        """Set the logging level based on debug setting."""
        self.logger.setLevel(10 if self.debug else 20)


# Factory functions for creating document scrapers
def create_document_scraper() -> SciScraper:
    """
    Create a scraper for analyzing PDF documents.

    Returns:
        Configured SciScraper for document analysis
    """
    # Create extractors
    directory_extractor = DirectoryExtractor(suffix="pdf")

    # Create analyzer
    document_analyzer = DocumentAnalyzer(
        target_words_file=Path(config.target_words).resolve(),
        excluded_words_file=Path(config.bycatch_words).resolve(),
    )

    # Create fetcher and pipeline
    fetcher = Fetcher(source=directory_extractor)

    def process_documents(files):
        """Process a list of PDF files."""
        results = []
        for pdf_path in files:
            try:
                result = document_analyzer.analyze_pdf(pdf_path)
                identifier_result = IdentifierExtractor().extract_from_pdf(
                    pdf_path
                )

                # Convert to dictionary for DataFrame creation
                result_dict = {
                    "doi_from_pdf": (
                        identifier_result.identifier
                        if identifier_result
                        else "N/A"
                    ),
                    "matching_terms": result.target_matches.total_matches,
                    "bycatch_terms": result.excluded_matches.total_matches,
                    "total_word_count": result.word_count,
                    "wordscore": result.relevance_score,
                    "target_terms_top_3": (
                        result.target_matches.get_top_matches(3)
                    ),
                    "bycatch_terms_top_3": (
                        result.excluded_matches.get_top_matches(3)
                    ),
                    "paper_parentheticals": result.parenthetical_phrases,
                }
                results.append(result_dict)
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")

        return results

    pipeline = Pipeline(
        fetcher=fetcher,
        transformers=[
            process_documents,
            remove_empty_columns,
            optimize_dtypes,
        ],
    )

    return SciScraper(pipeline=pipeline)


def create_semantic_search_scraper() -> SciScraper:
    """
    Create a scraper for searching Semantic Scholar.

    Returns:
        Configured SciScraper for Semantic Scholar searches
    """
    # Create extractors
    csv_extractor = CsvColumnExtractor(column="title")

    # Create Semantic Scholar scraper
    semantic_scraper = create_semantic_scholar_scraper()

    # Create fetcher and pipeline
    fetcher = Fetcher(source=csv_extractor)

    def search_semantic_scholar(queries):
        """Search Semantic Scholar for each query."""
        results = []
        for query in queries:
            try:
                for publication in semantic_scraper.search(query):
                    results.append(publication.to_dict())
            except Exception as e:
                logger.error(f"Failed to search for {query}: {e}")

        return results

    pipeline = Pipeline(
        fetcher=fetcher,
        transformers=[
            search_semantic_scholar,
            remove_empty_columns,
            optimize_dtypes,
        ],
    )

    return SciScraper(pipeline=pipeline)


def create_citation_scraper() -> SciScraper:
    """
    Create a scraper for extracting citations.

    Returns:
        Configured SciScraper for citation extraction
    """
    # Create extractors
    csv_extractor = CsvColumnExtractor(column="doi")

    # Create Semantic Scholar scraper
    semantic_scraper = create_semantic_scholar_scraper()

    # Create fetcher and pipeline
    fetcher = Fetcher(source=csv_extractor)

    def fetch_citations(dois):
        """Fetch citations for each DOI."""
        results = []
        for doi in dois:
            try:
                publication = semantic_scraper.fetch_publication(doi)
                if publication:
                    for citation in publication.citations:
                        results.append(
                            {
                                "citation": citation,
                                "source_title": publication.title,
                            }
                        )
            except Exception as e:
                logger.error(f"Failed to fetch citations for {doi}: {e}")

        return results

    pipeline = Pipeline(
        fetcher=fetcher,
        transformers=[
            fetch_citations,
            remove_empty_columns,
            optimize_dtypes,
        ],
    )

    return SciScraper(pipeline=pipeline)


def create_reference_scraper() -> SciScraper:
    """
    Create a scraper for extracting references.

    Returns:
        Configured SciScraper for reference extraction
    """
    # Create extractors
    csv_extractor = CsvColumnExtractor(column="doi")

    # Create Semantic Scholar scraper
    semantic_scraper = create_semantic_scholar_scraper()

    # Create fetcher and pipeline
    fetcher = Fetcher(source=csv_extractor)

    def fetch_references(dois):
        """Fetch references for each DOI."""
        results = []
        for doi in dois:
            try:
                publication = semantic_scraper.fetch_publication(doi)
                if publication:
                    for reference in publication.references:
                        results.append(
                            {
                                "reference": reference,
                                "source_title": publication.title,
                            }
                        )
            except Exception as e:
                logger.error(f"Failed to fetch references for {doi}: {e}")

        return results

    pipeline = Pipeline(
        fetcher=fetcher,
        transformers=[
            fetch_references,
            remove_empty_columns,
            optimize_dtypes,
        ],
    )

    return SciScraper(pipeline=pipeline)


def create_author_scraper() -> SciScraper:
    """
    Create a scraper for author information.

    Returns:
        Configured SciScraper for author information
    """
    # Create extractors
    csv_extractor = CsvColumnExtractor(column="author_list")

    # Create ORCID scraper
    orcid_scraper = create_orcid_scraper()

    # Create fetcher and pipeline
    fetcher = Fetcher(source=csv_extractor)

    def search_authors(authors):
        """Search for author information."""
        results = []
        for author in authors:
            try:
                for publication in orcid_scraper.search(author):
                    results.append(publication.to_dict())
            except Exception as e:
                logger.error(f"Failed to search for author {author}: {e}")

        return results

    pipeline = Pipeline(
        fetcher=fetcher,
        transformers=[
            search_authors,
            remove_empty_columns,
            optimize_dtypes,
        ],
    )

    return SciScraper(pipeline=pipeline)


def create_download_scraper() -> SciScraper:
    """
    Create a scraper for downloading papers.

    Returns:
        Configured SciScraper for paper downloads
    """
    # Create extractors
    csv_extractor = CsvColumnExtractor(column="doi")

    # Create paper downloader
    paper_downloader = create_paper_downloader()

    # Create fetcher and pipeline
    fetcher = Fetcher(source=csv_extractor)

    def download_papers(dois):
        """Download papers for each DOI."""
        results = []
        for doi in dois:
            try:
                result = paper_downloader.download(doi)
                results.append(
                    {
                        "doi": doi,
                        "success": result.success,
                        "filepath": (
                            str(result.file_path)
                            if result.file_path
                            else "N/A"
                        ),
                        "downloader": result.downloader_name,
                        "error": result.error_message,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to download paper {doi}: {e}")
                results.append(
                    {
                        "doi": doi,
                        "success": False,
                        "filepath": "N/A",
                        "downloader": paper_downloader.name,
                        "error": str(e),
                    }
                )

        return results

    pipeline = Pipeline(
        fetcher=fetcher,
        transformers=[
            download_papers,
            remove_empty_columns,
            optimize_dtypes,
        ],
    )

    return SciScraper(pipeline=pipeline)


def create_image_scraper() -> SciScraper:
    """
    Create a scraper for downloading images.

    Returns:
        Configured SciScraper for image downloads
    """
    # Create extractors
    csv_extractor = CsvColumnExtractor(column="figures")

    # Create image downloader
    image_downloader = create_image_downloader()

    # Create fetcher and pipeline
    fetcher = Fetcher(source=csv_extractor)

    def download_images(image_urls):
        """Download images from URLs."""
        results = []
        for url in image_urls:
            if not url or url == "N/A":
                continue

            try:
                result = image_downloader.download(url)
                results.append(
                    {
                        "url": url,
                        "success": result.success,
                        "filepath": (
                            str(result.file_path)
                            if result.file_path
                            else "N/A"
                        ),
                        "downloader": result.downloader_name,
                        "error": result.error_message,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to download image {url}: {e}")
                results.append(
                    {
                        "url": url,
                        "success": False,
                        "filepath": "N/A",
                        "downloader": image_downloader.name,
                        "error": str(e),
                    }
                )

        return results

    pipeline = Pipeline(
        fetcher=fetcher,
        transformers=[
            download_images,
            remove_empty_columns,
            optimize_dtypes,
        ],
    )

    return SciScraper(pipeline=pipeline)


def create_abstract_scraper() -> SciScraper:
    """
    Create a scraper for analyzing abstracts.

    Returns:
        Configured SciScraper for abstract analysis
    """
    # Create extractors
    csv_extractor = CsvColumnExtractor(column="abstract")

    # Create document analyzer
    document_analyzer = DocumentAnalyzer(
        target_words_file=Path(config.target_words).resolve(),
        excluded_words_file=Path(config.bycatch_words).resolve(),
    )

    # Create fetcher and pipeline
    fetcher = Fetcher(source=csv_extractor)

    def analyze_abstracts(abstracts):
        """Analyze abstracts for relevance."""
        results = []
        for abstract in abstracts:
            try:
                if not abstract or abstract == "N/A":
                    continue

                result = document_analyzer.analyze_text(abstract)

                # Convert to dictionary for DataFrame creation
                result_dict = {
                    "abstract": (
                        abstract[:100] + "..."
                        if len(abstract) > 100
                        else abstract
                    ),
                    "matching_terms": result.target_matches.total_matches,
                    "bycatch_terms": result.excluded_matches.total_matches,
                    "total_word_count": result.word_count,
                    "wordscore": result.relevance_score,
                    "target_terms_top_3": (
                        result.target_matches.get_top_matches(3)
                    ),
                    "bycatch_terms_top_3": (
                        result.excluded_matches.get_top_matches(3)
                    ),
                }
                results.append(result_dict)
            except Exception as e:
                logger.error(f"Failed to analyze abstract: {e}")

        return results

    pipeline = Pipeline(
        fetcher=fetcher,
        transformers=[
            analyze_abstracts,
            remove_empty_columns,
            optimize_dtypes,
        ],
    )

    return SciScraper(pipeline=pipeline)


# Dictionary of available scrapers
SCISCRAPERS: Dict[str, SciScraper] = {
    "directory": create_document_scraper(),
    "csv": create_semantic_search_scraper(),
    "citations": create_citation_scraper(),
    "references": create_reference_scraper(),
    "orcid": create_author_scraper(),
    "download": create_download_scraper(),
    "images": create_image_scraper(),
    "wordscore": create_abstract_scraper(),
    "fastscore": create_abstract_scraper(),  # Alias for wordscore
}


def read_factory() -> SciScraper:
    """
    Create a scraper based on user input.

    Returns:
        Configured SciScraper
    """
    while True:
        scrape_process = input(
            f"Enter desired data scraping process ({', '.join(SCISCRAPERS)}): "
        )
        try:
            return SCISCRAPERS[scrape_process]
        except KeyError:
            logger.error(
                "Unknown data scraping process option: %s.", scrape_process
            )
