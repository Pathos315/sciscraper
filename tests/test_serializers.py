import pytest
from sciscrape.serials import serialize_from_csv, serialize_from_directory


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
                "I. Ron Butterfly",
            ],
        ),
    ),
)
def test_serialize_from_csv(mock_csv, column, expected):
    output = serialize_from_csv(mock_csv, column=column)
    assert isinstance(output, list)
    assert output == expected


def test_serialize_from_csv_type_error(mock_csv):
    with pytest.raises(TypeError):
        serialize_from_csv(mock_csv, "times_cited")


def test_serialize_from_directory():
    test_dir = "tests/test_dirs"
    file = "tests/test_dirs/test_pdf_1.pdf"
    output = serialize_from_directory(test_dir)
    assert output == [file]


def test_serialize_from_directory_len_error(tmpdir):
    with pytest.raises(ValueError):
        serialize_from_directory(tmpdir)