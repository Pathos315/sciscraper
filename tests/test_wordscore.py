import pytest
from sciscrape.wordscore import RelevanceCalculator


"""def test_wordscore_non_zero(wordscore_calc):
    wordscore = [wordscore_calc() for _ in range(255)]
    assert any(bool(score <= 0.00) for score in wordscore) != True
    assert all(bool(score >= 0.00) for score in wordscore)
    assert all(isinstance(score, float) for score in wordscore)
    del wordscore
"""


def test_calc_odds(wordscore_calc):
    odds_list = [
        wordscore_calc.calc_odds(wordscore_calc.pos_part, wordscore_calc.neg_part)
        for _ in range(255)
    ]
    assert all(isinstance(odds, float) for odds in odds_list)
    del odds_list


def test_wordscore_div_zero_raw_score():
    with pytest.raises(ZeroDivisionError):
        return 0 / (0 + 0)


def test_wordscore_creation(wordscore_dict):
    wordscore_b = RelevanceCalculator.from_dict(wordscore_dict)
    assert wordscore_b.to_dict() == wordscore_dict


def test_zero_division_final_score(wordscore_calc):
    with pytest.raises(ZeroDivisionError):
        wordscore_calc(0, 0, 0)
