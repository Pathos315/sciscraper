import pytest

from sciscrape.stagers import stage_from_series, stage_with_reference


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
def test_stage_from_series(mock_dataframe, column, expected):
    output = stage_from_series(mock_dataframe, column=column)
    assert isinstance(output, list)
    assert output == expected


@pytest.mark.xfail
def test_serialize_from_csv_type_error(mock_dataframe):
    with pytest.raises(AttributeError):
        stage_from_series(mock_dataframe, "times_cited")


def test_valid_stagers(mock_dataframe):
    output = stage_with_reference(
        mock_dataframe, column_x="listed_data", column_y="title"
    )
    assert isinstance(output, tuple)
    assert output == (
        [
            "['pub.10001', 'pub.10002', 'pub.10003']",
            "['pub.10004', 'pub.10005']",
            "N/A",
            "['pub.10008']",
        ],
        [
            "Fake News and Misinformation",
            "Prosocial Eurythmics",
            "Gamification on Social Media",
            "Memoirs of a Gaysha, Jujubee's Journey, I'm Still Here",
        ],
    )
