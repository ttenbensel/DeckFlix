from deckflix_app.library import LibraryIndex
from deckflix_app.metadata.parser import parse_filename


def test_add_and_find():
    index = LibraryIndex()

    movie = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    index.add(movie)

    result = index.find(movie)

    assert result is movie


def test_not_found():
    index = LibraryIndex()

    avatar = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    alien = parse_filename(
        "Alien (1979) 1080p BluRay HEVC.mkv"
    )

    index.add(avatar)

    assert index.find(alien) is None
