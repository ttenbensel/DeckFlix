from pathlib import Path

from deckflix_app.scanner import (
    metadata_from_file,
)


def test_special_in_explicit_season_directory_is_tv_special(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "The Walking Dead"
        / "Season 4"
        / (
            "The.Walking.Dead.S04.Special."
            "Inside.The.Walking.Dead."
            "Walker.University.HDTV.x264-W4F.mp4"
        )
    )

    path.parent.mkdir(
        parents=True
    )
    path.touch()

    media = metadata_from_file(
        path
    )

    assert media.media_type == "tv"
    assert media.title == "The Walking Dead"
    assert media.content_type == "special"
    assert media.season is None
    assert media.episode is None


def test_plain_named_special_preserves_existing_parser_behavior(
    tmp_path: Path,
):
    """
    Existing DeckFlix behaviour treats an explicit title
    containing "Special" as TV special content.

    5G.13D must not change that established behaviour merely
    to add Season-directory contextual recognition.
    """
    path = (
        tmp_path
        / "Movies"
        / "Example Special.mp4"
    )

    path.parent.mkdir(
        parents=True
    )
    path.touch()

    media = metadata_from_file(
        path
    )

    assert media.media_type == "tv"
    assert media.content_type == "special"
    assert media.season is None
    assert media.episode is None


def test_season_directory_alone_does_not_promote_title_only_file(
    tmp_path: Path,
):
    """
    A Season directory by itself is not enough evidence to
    invent a TV episode or special identity.
    """
    path = (
        tmp_path
        / "Example Show"
        / "Season 4"
        / "Behind The Story.mp4"
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


def test_sxxxyyy_conservative_identity_is_preserved(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "Adventure Time"
        / "Season 6"
        / "Adventure Time S06X01 Special.mp4"
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


def test_extra_wins_before_contextual_special(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "Example Show"
        / "Season 4"
        / "Extras"
        / "Special Feature.mp4"
    )

    path.parent.mkdir(
        parents=True
    )
    path.touch()

    media = metadata_from_file(
        path
    )

    assert media.media_type == "tv"
    assert media.content_type == "extra"
    assert media.season is None
    assert media.episode is None


def test_episode_zero_preserves_existing_identity(
    tmp_path: Path,
):
    """
    DeckFlix already represents explicit SxxE00 files as
    episode-zero identities.

    Other safety layers treat episode zero conservatively, so
    5G.13D must not silently change that representation.
    """
    path = (
        tmp_path
        / "The Walking Dead"
        / "Season 4"
        / (
            "The.Walking.Dead.S04E00."
            "Inside.the.Walking.Dead."
            "PROPER.HDTV.x264-BATV.mp4"
        )
    )

    path.parent.mkdir(
        parents=True
    )
    path.touch()

    media = metadata_from_file(
        path
    )

    assert media.media_type == "tv"
    assert media.content_type == "episode"
    assert media.season == 4
    assert media.episode == 0
