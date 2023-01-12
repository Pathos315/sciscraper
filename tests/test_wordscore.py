import pytest
from sciscrape.wordscore import WordscoreCalculator
import unittest

calculator = WordscoreCalculator(10, 5, 100)


@pytest.mark.parametrize(
    (
        "target",
        "bycatch",
        "total_length",
    ),
    (
        (10, 5, 100),
        (5, 15, 50),
        (1, 2, 50),
    ),
)
def test_wordscore_calculator_initialization(
    target,
    bycatch,
    total_length,
):
    calculator = WordscoreCalculator(
        target,
        bycatch,
        total_length,
    )
    assert calculator.target_count == target
    assert calculator.bycatch_count == bycatch
    assert calculator.total_length == total_length


@pytest.mark.parametrize(
    (
        "prior",
        "likelihood",
        "margin",
        "expected",
    ),
    (
        (0.5, 0.8, 0.3, 0.5714285714285715),
        (0.1, 0.3, 0.5, 0.056603773584905655),
        (0.9, 0.8, 0.2, 0.7826086956521738),
    ),
)
def test_bayes_theorem(prior, likelihood, margin, expected):
    result = calculator.bayes_theorem(
        prior=prior,
        likelihood=likelihood,
        margin=margin,
    )
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    (
        "part",
        "whole",
        "expected",
    ),
    (
        (2, 4, 0.25),
        (5, 10, 0.03125),
        (8, 15, 0.006546208346288674),
    ),
)
def test_get_margin(part, whole, expected):
    result = calculator.get_margin(part, whole)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    ("success_margin", "failure_margin", "expected"),
    (
        (0.1, 0.2, 346206189128.80005),
        (0.2, 0.3, 1038618567386.3999),
        (0.3, 0.4, 2077237134772.8),
    ),
)
def test_get_likelihood(success_margin, failure_margin, expected):
    result = calculator.get_likelihood(success_margin, failure_margin)
    assert result == pytest.approx(expected, abs=1e-4)
