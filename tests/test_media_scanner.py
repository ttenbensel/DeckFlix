from pathlib import Path

from deckflix_app.scanner import (
    metadata_from_file,
    scan_media,
)


def test_scan_media(
    tmp_path: Path,
):
    (
        tmp_path
        / "Avatar (2009) 1080p BluRay HEVC.mkv"
    ).touch()

    (
        tmp_path
        / "Alien (1979) 720p WEB-DL x264.mp4"
    ).touch()

    media = scan_media(
        tmp_path
    )

    assert len(media) == 2

    titles = {
        item.title
        for item in media
    }

    assert "Avatar" in titles
    assert "Alien" in titles

    for item in media:
        assert item.path is not None
        assert item.size >= 0


def test_aac_5_1_movie_is_not_tv(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Dune (2021)"
        / (
            "Dune.2021.1080p.WEBRip."
            "x264.AAC5.1-[YTS.MX].mp4"
        )
    )

    file.parent.mkdir()
    file.touch()

    media = metadata_from_file(
        file
    )

    assert media.media_type == "movie"
    assert media.title == "Dune"
    assert media.year == 2021
    assert media.season is None
    assert media.episode is None


def test_numeric_movie_with_aac_5_1_is_not_tv(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "65 (2023)"
        / (
            "65.2023.1080p.WEBRip."
            "x264.AAC5.1-[YTS.MX].mp4"
        )
    )

    file.parent.mkdir()
    file.touch()

    media = metadata_from_file(
        file
    )

    assert media.media_type == "movie"
    assert media.title == "65"
    assert media.year == 2023
    assert media.season is None
    assert media.episode is None


def test_band_of_brothers_part_in_season_directory(
    tmp_path: Path,
):
    folder = (
        tmp_path
        / "Band of Brothers"
        / "Season 01"
    )

    folder.mkdir(
        parents=True
    )

    for number in range(1, 4):
        (
            folder
            / (
                "Band of Brothers "
                f"- Part {number:02d}.avi"
            )
        ).touch()

    media = metadata_from_file(
        folder
        / "Band of Brothers - Part 01.avi"
    )

    assert media.media_type == "tv"
    assert media.title == "Band of Brothers"
    assert media.season == 1
    assert media.episode == 1


def test_banana_episode_word_is_tv(
    tmp_path: Path,
):
    folder = (
        tmp_path
        / "Banana (2015)"
    )

    folder.mkdir()

    for number in (
        4,
        7,
        8,
    ):
        (
            folder
            / f"Episode {number}.mp4"
        ).touch()

    media = metadata_from_file(
        folder
        / "Episode 4.mp4"
    )

    assert media.media_type == "tv"
    assert media.title == "Banana"
    assert media.season == 1
    assert media.episode == 4


def test_explicit_s00_episode_remains_tv(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "South Park"
        / "South.Park.S24E00.mkv"
    )

    file.parent.mkdir()
    file.touch()

    media = metadata_from_file(
        file
    )

    assert media.media_type == "tv"
    assert media.title == "South Park"
    assert media.season == 24
    assert media.episode == 0


def test_sxxxyyy_special_keeps_conservative_identity(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Adventure Time"
        / "Season 06"
        / (
            "Adventure Time S06X01 "
            "Special.mp4"
        )
    )

    file.parent.mkdir(
        parents=True
    )
    file.touch()

    media = metadata_from_file(
        file
    )

    assert media.media_type == "movie"
    assert "Special" in media.title
    assert media.season is None
    assert media.episode is None


def test_yts_5_1_folder_does_not_become_tv(
    tmp_path: Path,
):
    folder = (
        tmp_path
        / (
            "Dune (2021) [1080p] "
            "[WEBRip] [5.1] [YTS.MX]"
        )
    )

    folder.mkdir()

    file = (
        folder
        / (
            "Dune.2021.1080p.WEBRip."
            "x264.AAC5.1-[YTS.MX].mp4"
        )
    )

    file.touch()

    media = metadata_from_file(
        file
    )

    assert media.media_type == "movie"
    assert media.title == "Dune"
    assert media.year == 2021
    assert media.season is None
    assert media.episode is None


def test_hash_episode_scanner_identity(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Two and a Half Men"
        / "Season 5"
        / "Two.and.a.Half.Men.# 16.avi"
    )

    file.parent.mkdir(
        parents=True
    )
    file.touch()

    media = metadata_from_file(
        file
    )

    assert media.media_type == "tv"
    assert media.title == "Two and a Half Men"
    assert media.content_type == "episode"
    assert media.season == 5
    assert media.episode == 16


def test_existing_extra_protection_survives_hash_change(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Rick and Morty"
        / "Release"
        / "Extras"
        / "Behind The Scenes # 01.mkv"
    )

    file.parent.mkdir(
        parents=True
    )
    file.touch()

    media = metadata_from_file(
        file
    )

    assert media.media_type == "tv"
    assert media.title == "Rick and Morty"
    assert media.content_type == "extra"
    assert media.season is None
    assert media.episode is None
