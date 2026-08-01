from pathlib import Path

from deckflix_app.media import inspect_media
from deckflix_app.scanner import scan_videos


def test_tv_file_directly_inside_show_folder(tmp_path: Path):
    file = (
        tmp_path
        / "1000 ways to die"
        / "1000.ways.to.die.s05e20.hdtv.xvid.avi"
    )

    file.parent.mkdir()
    file.touch()

    media = inspect_media(file)

    assert media.media_type == "tv"
    assert media.title.lower() == "1000 ways to die"
    assert media.season == 5
    assert media.episode == 20


def test_numeric_tv_show_name_is_preserved(tmp_path: Path):
    file = (
        tmp_path
        / "1883.S01.COMPLETE.REPACK.1080p"
        / "1883.S01E02.Behind.Us.A.Cliff.mkv"
    )

    file.parent.mkdir()
    file.touch()

    media = inspect_media(file)

    assert media.title == "1883"
    assert media.season == 1
    assert media.episode == 2


def test_1923_show_name_is_preserved(tmp_path: Path):
    file = (
        tmp_path
        / "1923"
        / "1923.S01E01.WEB.x264.mkv"
    )

    file.parent.mkdir()
    file.touch()

    media = inspect_media(file)

    assert media.title == "1923"


def test_spaced_episode_filename_uses_filename_title(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "3 Body Problem - Season 1"
        / "3 Body Problem - S01E01 - Countdown.mkv"
    )

    file.parent.mkdir()
    file.touch()

    media = inspect_media(file)

    assert media.title == "3 Body Problem"


def test_scanner_ignores_sample_directories(tmp_path: Path):
    real = tmp_path / "Show" / "Show.S01E01.mkv"
    sample = (
        tmp_path
        / "Show"
        / "Release"
        / "Sample"
        / "show.s01e01-sample.avi"
    )

    real.parent.mkdir(parents=True)
    sample.parent.mkdir(parents=True)
    real.touch()
    sample.touch()

    files = scan_videos(tmp_path)

    assert real in files
    assert sample not in files


def test_two_by_episode_format_removes_episode_title(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Black Mirror"
        / "Black mirror 2"
        / "Black.Mirror.2x01.Be.Right.Back.720p.HDTV.x264-FoV.mkv"
    )

    file.parent.mkdir(parents=True)
    file.touch()

    media = inspect_media(file)

    assert media.title == "Black Mirror"
    assert media.season == 2
    assert media.episode == 1


def test_numeric_episode_filename_uses_release_folder_title(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "American Horror Story"
        / "American Horror Story - The Complete Season 4"
        / "American Horror Story S04E01 HDTV x264-LOL"
        / "american.horror.story.401.hdtv-lol.mp4"
    )

    file.parent.mkdir(parents=True)
    file.touch()

    media = inspect_media(file)

    assert media.title == "American Horror Story"
    assert media.season == 4
    assert media.episode == 1


def test_release_folder_beats_cryptic_filename(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "1000 ways to die"
        / "1000.Ways.To.Die.S05E07.HDTV.XviD-aAF"
        / "aaf-1wtd.s05e07.avi"
    )

    file.parent.mkdir(parents=True)
    file.touch()

    media = inspect_media(file)

    assert media.title == "1000 Ways To Die"
    assert media.season == 5
    assert media.episode == 7


def test_leading_file_order_number_is_removed(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "1000 ways to die"
        / "23_1000.ways.to.die.s05e22.hdtv.xvid.avi"
    )

    file.parent.mkdir(parents=True)
    file.touch()

    media = inspect_media(file)

    assert media.title.lower() == "1000 ways to die"
    assert media.season == 5
    assert media.episode == 22
