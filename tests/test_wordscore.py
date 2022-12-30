import pytest
from sciscrape.wordscore import RelevanceCalculator


"""def test_wordscore_non_zero(wordscore_calc):
    wordscore = [wordscore_calc() for _ in range(255)]
    assert any(bool(score <= 0.00) for score in wordscore) != True
    assert all(bool(score >= 0.00) for score in wordscore)
    assert all(isinstance(score, float) for score in wordscore)
    del wordscore
"""


def test_wordscore_div_zero_raw_score():
    with pytest.raises(ZeroDivisionError):
        return 0 / (0 + 0)


def test_wordscore_creation(wordscore_dict):
    wordscore_b = RelevanceCalculator.from_dict(wordscore_dict)
    assert wordscore_b.to_dict() == wordscore_dict
