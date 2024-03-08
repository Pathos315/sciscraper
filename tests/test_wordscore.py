import pytest

from src.docscraper import calculate_likelihood


@pytest.mark.parametrize(
    ("total_words", "match_words", "bycatch_words", "expected"),
    [
        (100, 20, 5, 0.5625),
        (1000, 500, 10, 0.7425),
        (0, 20, 5, 0.0),
        (100, -20, 5, 0.0),
        (100, 20, -5, 0.0),
        (100, 20, 80, 0.0),
        (100, 100, 0, 1.0),
        (100, 0, 0, 0.5),
        (1, 0, 0, 0.5),
    ],
)
def test_calculate_likelihood(
    total_words, match_words, bycatch_words, expected
):
    assert (
        calculate_likelihood(total_words, match_words, bycatch_words)
        == expected
    )


def test_calculate_likelihood_with_high_undesired_matches():
    likelihood = calculate_likelihood(100, 20, 80)
    assert 0 <= likelihood <= 1


def test_calculate_likelihood_with_all_undesired_matches():
    likelihood = calculate_likelihood(100, 0, 100)
    # Check if the likelihood is non-negative due to low weighting of undesired_matches
    assert likelihood >= 0


def test_calculate_likelihood_with_large_input():
    assert calculate_likelihood(10000, 5000, 2500) >= 0
