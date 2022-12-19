import sys
from setuptools import setup

vi = sys.version_info
if vi < (3, 7):
    raise RuntimeError("Sciscraper requires Python 3.7 or greater")


if __name__ == "__main__":
    setup()
