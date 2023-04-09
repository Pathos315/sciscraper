[![sciscraper](https://github.com/Pathos315/sciscraper/actions/workflows/tests.yaml/badge.svg)](https://github.com/Pathos315/sciscraper/actions/workflows/tests.yaml)

# sciscraper
`sciscraper` is a Python package and command line interface (CLI) for scraping scientific articles from various sources.
It should work on Python 3.8+; on MacOS, Windows, and Linux.

## Installation

You can install sciscraper via pip:

```pip install sciscraper```

## Usage

`sciscraper` offers the following scraping choices:
- directory: takes a directory of .pdf files, and returns a .csv file of bibliographic data for each;
- wordscore: takes a .csv file of bibliographic data for multiple papers and returns a .csv with a percentage value of its relevance to the configured query;
- citations: takes a .csv file of bibliographic data for multiple papers and returns a .csv of their citations (i.e. the ensuing papers that cited them);
- reference: takes a .csv file of bibliographic data for multiple papers and returns a .csv of their references (i.e. the papers that were referenced in the originals);
- download: *experimental* takes a .csv file of bibliographic data for multiple papers, attempts to download .pdfs of each into a directory; and,
- images: takes a .csv file of bibliographic data for multiple papers, attempts to download charts and figures of the papers from SemanticScholar.

You can initialize `sciscraper` from the terminal by entering `sciscraper` followed by `-m`, the designated scraping choice (see above), and the target file. For example:

```sciscraper -m directory <folder pathname goes here...>```

Or alternatively:
```sciscraper -m wordscore <filename.csv>```

And so forth.

### As Featured on ArjanCodes' Code Roast
- PART ONE: -> https://youtu.be/MXM6VEtf8SE
- PART TWO: -> https://www.youtube.com/watch?v=6ac4Um2Vicg

### Special Thanks
- ArjanCodes
- Michele Cotrufo
- Nathan Lippi
- Jon Watson Rooney
- Colin Meret
- James Murphy (mCoding)
- Micael Jarniac

### Maintainer
John Fallot
john.fallot@gmail.com

### License
[The MIT License](https://opensource.org/licenses/MIT)
Copyright (c) 2021-
John Fallot
