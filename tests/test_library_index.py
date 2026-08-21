from pathlib import Path

from deckflix_app.library import (
    LibraryIndex,
)
from deckflix_app.library.index import (
    media_key,
)
from deckflix_app.metadata.models import (
    MediaMetadata,
)
from deckflix_app.metadata.parser import (
    parse_filename,
)


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


def _special(
    path: str,
    *,
    title: str = "The Walking Dead",
) -> MediaMetadata:
    return MediaMetadata(
        media_type="tv",
        title=title,
        content_type="special",
        year=None,
        season=None,
        episode=None,
        path=Path(path),
    )


def test_different_unnumbered_specials_do_not_collide():
    index = LibraryIndex()

    preview = _special(
        "/library/The Walking Dead/Specials/"
        "The.Walking.Dead.S09E00.Season.9."
        "Preview.Special.720p.WEB.h264-TBS.mkv"
    )

    walker_university = _special(
        "/shuttle/The Walking Dead/Season 4/"
        "The.Walking.Dead.S04.Special.Inside."
        "The.Walking.Dead.Walker.University."
        "HDTV.x264-W4F.mp4"
    )

    index.add(preview)

    assert (
        media_key(preview)
        != media_key(walker_university)
    )

    assert (
        index.find(
            walker_university
        )
        is None
    )


def test_same_unnumbered_special_matches_across_roots():
    index = LibraryIndex()

    library = _special(
        "/library/The Walking Dead/Specials/"
        "The.Walking.Dead.S09E00.Season.9."
        "Preview.Special.720p.WEB.h264-TBS.mkv"
    )

    shuttle = _special(
        "/shuttle/The Walking Dead/Season 9/"
        "The.Walking.Dead.S09E00.Season.9."
        "Preview.Special.720p.WEB.h264-TBS.mkv"
    )

    index.add(library)

    assert (
        media_key(library)
        == media_key(shuttle)
    )

    assert (
        index.find(shuttle)
        is library
    )


def test_south_park_same_special_matches_across_roots():
    index = LibraryIndex()

    library = _special(
        "/library/South Park/Season 24/"
        "South.Park.S24E00.The.Pandemic."
        "Special.1080p.WEB.h264-BAE.mkv",
        title="South Park",
    )

    shuttle = _special(
        "/shuttle/South Park/"
        "South.Park.S24E00.The.Pandemic.Special."
        "1080p.WEB.h264-BAE/"
        "South.Park.S24E00.The.Pandemic."
        "Special.1080p.WEB.h264-BAE.mkv",
        title="South Park",
    )

    index.add(library)

    assert (
        index.find(shuttle)
        is library
    )


def test_unnumbered_special_without_path_fails_closed():
    index = LibraryIndex()

    library = MediaMetadata(
        media_type="tv",
        title="Example Show",
        content_type="special",
        season=None,
        episode=None,
        path=None,
    )

    incoming = MediaMetadata(
        media_type="tv",
        title="Example Show",
        content_type="special",
        season=None,
        episode=None,
        path=None,
    )

    index.add(library)

    assert index.find(incoming) is None


def test_numbered_tv_episode_identity_is_unchanged():
    index = LibraryIndex()

    library = MediaMetadata(
        media_type="tv",
        title="Example Show",
        content_type="episode",
        season=3,
        episode=7,
        path=Path(
            "/library/Example Show/"
            "Season 03/S03E07.mkv"
        ),
    )

    incoming = MediaMetadata(
        media_type="tv",
        title="Example Show",
        content_type="episode",
        season=3,
        episode=7,
        path=Path(
            "/shuttle/Example Show/"
            "Season 3/S03E07.mp4"
        ),
    )

    index.add(library)

    assert (
        media_key(library)
        == (
            "tv",
            "example show",
            3,
            7,
        )
    )

    assert (
        index.find(incoming)
        is library
    )


def test_movie_identity_is_unchanged():
    movie = MediaMetadata(
        media_type="movie",
        title="Avatar",
        content_type="movie",
        year=2009,
        path=Path(
            "/movies/Avatar.mkv"
        ),
    )

    assert (
        media_key(movie)
        == (
            "movie",
            "avatar",
            2009,
        )
    )
