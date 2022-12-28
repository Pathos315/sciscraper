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


def test_len_factor(wordscore_calc):
    len_factor = (wordscore_calc.get_len_factor() for _ in range(255))
    assert all(isinstance(length, float) for length in len_factor)
    del len_factor


def test_wordscore_div_zero():
    with pytest.raises(ZeroDivisionError):
        RelevanceCalculator.calc_odds(15, 0)


def test_wordscore_div_zero_raw_score():
    with pytest.raises(ZeroDivisionError):
        return 0 / (0 + 0)


def test_wordscore_creation(wordscore_dict):
    wordscore_b = RelevanceCalculator.from_dict(wordscore_dict)
    assert wordscore_b.to_dict() == wordscore_dict


@pytest.mark.parametrize(
    ("pos_odds", "neg_odds", "len_factor", "expected"),
    (
        (1, 1, 1, 0.5),
        (1, 2, 1, 0.3333333333333333),
        (2, 1, 1, 0.6666666666666666),
        (2, 2, 1, 0.5),
        (1, 1, 2, 1.0),
        (1, 2, 2, 0.6666666666666666),
        (2, 2, 2, 1.0),
    ),
)
def test_calculate_final_score(
    wordscore_calc, pos_odds, neg_odds, len_factor, expected
):
    assert (
        wordscore_calc.calculate_final_score(pos_odds, neg_odds, len_factor) == expected
    )


def test_zero_division_final_score(wordscore_calc):
    with pytest.raises(ZeroDivisionError):
        wordscore_calc.calculate_final_score(0, 0, 0)
