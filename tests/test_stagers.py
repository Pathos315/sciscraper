from pandas import DataFrame
import pytest

from sciscrape.stagers import stage_from_series


@pytest.mark.skip
@pytest.mark.parametrize(
    ("column", "expected"),
    (
        (
            "title",
            [
                "Fake News and Misinformation",
                "Prosocial Eurythmics",
                "Gamification on Social Media",
                "Memoirs of a Gaysha, Jujubee's Journey, I'm Still Here",
            ],
        ),
        (
            "doi",
            [
                "10.1000/12345",
                "10.1000/23456",
                "10.1000/34567",
                "pub.12345",
            ],
        ),
        (
            "authors",
            [
                "Darius Lettsgetham",
                "Anne Elon-Ux",
                "Jujubee",
            ],
        ),
    ),
)
def test_stage_from_series(mock_dataframe: DataFrame, column, expected):
    output = stage_from_series(mock_dataframe, column=column)
    assert isinstance(output, list)
    assert output == expected

