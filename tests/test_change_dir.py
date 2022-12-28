from sciscrape.change_dir import change_dir
from os import getcwd


def test_change_dir(mock_dirs):
    initial_directory: str = getcwd()
    with change_dir(mock_dirs):
        new_directory: str = getcwd()
        assert initial_directory != new_directory
    final_directory = getcwd()
    assert initial_directory == final_directory
