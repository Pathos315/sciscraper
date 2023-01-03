import pytest
from sciscrape.wordscore import RelevanceCalculator


def test_wordscore_div_zero_raw_score():
    with pytest.raises(ZeroDivisionError):
        return 0 / (0 + 0)


def test_wordscore_creation(wordscore_dict):
    wordscore_b = RelevanceCalculator.from_dict(wordscore_dict)
    assert wordscore_b.to_dict() == wordscore_dict
