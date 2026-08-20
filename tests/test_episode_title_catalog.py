from pathlib import Path

from deckflix_app.metadata.episode_catalog import (
    resolve_title_only_episode,
)
from deckflix_app.scanner import (
    metadata_from_file,
)


SEASON_9 = [
    ("The City Of New York vs. Homer Simpson", 1),
    ("The Principal And The Pauper", 2),
    ("Lisa's Sax", 3),
    ("Treehouse Of Horror VIII", 4),
    ("The Cartridge Family", 5),
    ("Bart Star", 6),
    ("The Two Mrs. Nahasapeemapetilons", 7),
    ("Lisa The Skeptic", 8),
    ("Realty Bites", 9),
    ("Miracle On Evergreen Terrace", 10),
    ("All Singing, All Dancing", 11),
    ("Bart Carny", 12),
    ("The Joy Of Sect", 13),
    ("Das Bus", 14),
    ("The Last Temptation Of Krust", 15),
    ("Dumbell Indemnity", 16),
    ("Lisa The Simpson", 17),
    ("This Little Wiggy", 18),
    ("Simpson Tide", 19),
    ("The Trouble With Trillions", 20),
    ("Girly Edition", 21),
    ("Trash Of The Titans", 22),
    ("King Of The Hill", 23),
    ("Lost Our Lisa", 24),
    ("Natural Born Kissers", 25),
]


def _file(
    tmp_path: Path,
    title: str,
    *,
    season: int = 9,
) -> Path:
    path = (
        tmp_path
        / "The Simpsons"
        / f"Season {season}"
        / f"{title}.m4v"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.touch()

    return path


def test_all_simpsons_season_9_titles_resolve(
    tmp_path: Path,
):
    for title, expected_episode in SEASON_9:
        path = _file(
            tmp_path,
            title,
        )

        identity = resolve_title_only_episode(
            path,
            candidate_title=title,
        )

        assert identity is not None
        assert identity.title == "The Simpsons"
        assert identity.season == 9
        assert (
            identity.episode
            == expected_episode
        )


def test_scanner_promotes_catalog_match_to_episode(
    tmp_path: Path,
):
    path = _file(
        tmp_path,
        "Bart Carny",
    )

    media = metadata_from_file(
        path
    )

    assert media.media_type == "tv"
    assert media.title == "The Simpsons"
    assert media.content_type == "episode"
    assert media.season == 9
    assert media.episode == 12


def test_known_shuttle_misspelling_is_explicit_alias(
    tmp_path: Path,
):
    path = _file(
        tmp_path,
        "Dumbell Indemnity",
    )

    media = metadata_from_file(
        path
    )

    assert media.media_type == "tv"
    assert media.title == "The Simpsons"
    assert media.season == 9
    assert media.episode == 16


def test_unknown_title_fails_closed(
    tmp_path: Path,
):
    path = _file(
        tmp_path,
        "Definitely Not A Real Episode",
    )

    media = metadata_from_file(
        path
    )

    assert media.media_type == "movie"
    assert media.season is None
    assert media.episode is None


def test_catalog_does_not_apply_to_wrong_season(
    tmp_path: Path,
):
    path = _file(
        tmp_path,
        "Bart Carny",
        season=8,
    )

    media = metadata_from_file(
        path
    )

    assert media.media_type == "movie"
    assert media.season is None
    assert media.episode is None


def test_catalog_does_not_apply_to_wrong_series(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "Another Show"
        / "Season 9"
        / "Bart Carny.m4v"
    )

    path.parent.mkdir(
        parents=True
    )

    path.touch()

    media = metadata_from_file(
        path
    )

    assert media.media_type == "movie"
    assert media.season is None
    assert media.episode is None


def test_extra_still_wins_before_title_catalog(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "The Simpsons"
        / "Release"
        / "Extras"
        / "Bart Carny.m4v"
    )

    path.parent.mkdir(
        parents=True
    )

    path.touch()

    media = metadata_from_file(
        path
    )

    assert media.media_type == "tv"
    assert media.title == "The Simpsons"
    assert media.content_type == "extra"
    assert media.season is None
    assert media.episode is None
