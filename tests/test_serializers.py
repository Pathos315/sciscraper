from pathlib import Path

import pytest

from sciscrape.serials import serialize_from_csv, serialize_from_directory


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
def test_serialize_from_csv(mock_csv, column, expected):
    output = serialize_from_csv(mock_csv, column=column)
    assert isinstance(output, list)
    assert output == expected


@pytest.mark.skip
def test_serialize_from_csv_attr_error(mock_csv):
    with pytest.raises(AttributeError):
        serialize_from_csv(mock_csv, "times_cited")


@pytest.mark.skip
def test_serialize_from_directory():
    test_path = Path("tests/test_dirs/")
    test_path = test_path / "test.pdf"
    output = serialize_from_directory(test_path)

    assert output == test_path
