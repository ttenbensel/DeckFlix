from pathlib import Path

from deckflix_app.media import inspect_media
from deckflix_app.scanner import scan_videos


def test_tv_file_directly_inside_show_folder(
    tmp_path: Path,
):
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


def test_numeric_tv_show_name_is_preserved(
    tmp_path: Path,
):
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


def test_1923_show_name_is_preserved(
    tmp_path: Path,
):
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


def test_scanner_ignores_sample_directories(
    tmp_path: Path,
):
    real = (
        tmp_path
        / "Show"
        / "Show.S01E01.mkv"
    )

    sample = (
        tmp_path
        / "Show"
        / "Release"
        / "Sample"
        / "show.s01e01-sample.avi"
    )

    real.parent.mkdir(
        parents=True
    )

    sample.parent.mkdir(
        parents=True
    )

    real.touch()
    sample.touch()

    files = scan_videos(
        tmp_path
    )

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

    file.parent.mkdir(
        parents=True
    )

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

    file.parent.mkdir(
        parents=True
    )

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

    file.parent.mkdir(
        parents=True
    )

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

    file.parent.mkdir(
        parents=True
    )

    file.touch()

    media = inspect_media(file)

    assert media.title.lower() == "1000 ways to die"
    assert media.season == 5
    assert media.episode == 22


def test_band_of_brothers_part_files_are_tv(
    tmp_path: Path,
):
    folder = (
        tmp_path
        / "Band of Brothers"
    )

    folder.mkdir()

    for number in range(1, 4):
        (
            folder
            / f"Band of Brothers - Part {number:02d}.avi"
        ).touch()

    media = inspect_media(
        folder
        / "Band of Brothers - Part 01.avi"
    )

    assert media.media_type == "tv"
    assert media.title == "Band of Brothers"
    assert media.season == 1
    assert media.episode == 1


def test_bikie_wars_part_files_are_tv(
    tmp_path: Path,
):
    folder = (
        tmp_path
        / "Bikie Wars"
    )

    folder.mkdir()

    for number in range(1, 4):
        (
            folder
            / (
                "Bikie Wars (Brothers in Arms) "
                f"- Part {number:02d}.mp4"
            )
        ).touch()

    media = inspect_media(
        folder
        / (
            "Bikie Wars (Brothers in Arms) "
            "- Part 02.mp4"
        )
    )

    assert media.media_type == "tv"
    assert media.title == "Bikie Wars"
    assert media.season == 1
    assert media.episode == 2


def test_episode_word_uses_parent_show_context(
    tmp_path: Path,
):
    folder = (
        tmp_path
        / "Banana"
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

    media = inspect_media(
        folder
        / "Episode 4.mp4"
    )

    assert media.media_type == "tv"
    assert media.title == "Banana"
    assert media.season == 1
    assert media.episode == 4


def test_spartacus_gods_of_arena_episode_format(
    tmp_path: Path,
):
    folder = (
        tmp_path
        / (
            "Spartacus Season 2 Prequel "
            "- Gods of the Arena"
        )
    )

    folder.mkdir()

    for number in range(1, 4):
        (
            folder
            / (
                "Spartacus Gods of the Arena "
                f"Episode {number:02d} - Test.avi"
            )
        ).touch()

    media = inspect_media(
        folder
        / (
            "Spartacus Gods of the Arena "
            "Episode 01 - Test.avi"
        )
    )

    assert media.media_type == "tv"
    assert media.title == "Spartacus Gods of the Arena"
    assert media.season == 1
    assert media.episode == 1


def test_extras_keep_series_identity(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Rick and Morty"
        / (
            "Rick and Morty Season 1 "
            "1080p HEVC"
        )
        / "Extras"
        / "Behind The Scenes 720p.mkv"
    )

    file.parent.mkdir(
        parents=True
    )

    file.touch()

    media = inspect_media(
        file
    )

    assert media.media_type == "movie"
    assert media.title == "Rick and Morty Extras"


def test_extras_from_different_series_do_not_share_key(
    tmp_path: Path,
):
    rick = (
        tmp_path
        / "Rick and Morty"
        / "Release"
        / "Extras"
        / "Behind The Scenes.mkv"
    )

    spartacus = (
        tmp_path
        / "Spartacus"
        / "Extras"
        / "Trailer.avi"
    )

    rick.parent.mkdir(
        parents=True
    )

    spartacus.parent.mkdir(
        parents=True
    )

    rick.touch()
    spartacus.touch()

    rick_media = inspect_media(
        rick
    )

    spartacus_media = inspect_media(
        spartacus
    )

    assert rick_media.key != spartacus_media.key
    assert rick_media.title == "Rick and Morty Extras"
    assert spartacus_media.title == "Spartacus Extras"


def test_sxxxyyy_special_not_equal_to_regular_episode(
    tmp_path: Path,
):
    special = (
        tmp_path
        / "Adventure Time"
        / "Season 07"
        / (
            "Adventure Time S07X01 "
            "Frog Seasons Spring.mp4"
        )
    )

    regular = (
        tmp_path
        / "Adventure Time"
        / "Season 07"
        / (
            "Adventure Time S07E01 "
            "Bonnie and Neddy.mp4"
        )
    )

    special.parent.mkdir(
        parents=True
    )

    special.touch()
    regular.touch()

    special_media = inspect_media(
        special
    )

    regular_media = inspect_media(
        regular
    )

    assert special_media.key != regular_media.key
    assert regular_media.media_type == "tv"
    assert regular_media.season == 7
    assert regular_media.episode == 1


def test_season_resolution_is_not_episode(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Game of Thrones"
        / (
            "Game.of.Thrones.The.Politics."
            "of.Power.A.Lookback.At."
            "Season.3.720p.HDTV.x264.mkv"
        )
    )

    file.parent.mkdir()

    file.touch()

    media = inspect_media(
        file
    )

    assert media.media_type == "movie"
    assert media.season is None
    assert media.episode is None


def test_s00_parent_and_e01_filename_becomes_special_episode(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "South Park"
        / (
            "South Park S00 "
            "The Spirit of Christmas"
        )
        / (
            "The Spirit of Christmas "
            "E01 Jesus vs Frosty.mp4"
        )
    )

    file.parent.mkdir(
        parents=True
    )

    file.touch()

    media = inspect_media(
        file
    )

    assert media.media_type == "tv"
    assert media.title == "South Park"
    assert media.season == 0
    assert media.episode == 1


def test_hash_episode_uses_explicit_season_directory(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Two and a Half Men"
        / "Season 5"
        / "Two.and.a.Half.Men.# 01.avi"
    )

    file.parent.mkdir(
        parents=True
    )
    file.touch()

    media = inspect_media(
        file
    )

    assert media.media_type == "tv"
    assert media.title == "Two and a Half Men"
    assert media.season == 5
    assert media.episode == 1


def test_hash_episode_preserves_double_digit_episode(
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

    media = inspect_media(
        file
    )

    assert media.media_type == "tv"
    assert media.title == "Two and a Half Men"
    assert media.season == 5
    assert media.episode == 16


def test_hash_number_without_season_context_is_not_promoted(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "Movie Collection"
        / "Example # 01.avi"
    )

    file.parent.mkdir(
        parents=True
    )
    file.touch()

    media = inspect_media(
        file
    )

    assert media.media_type == "movie"
    assert media.season is None
    assert media.episode is None


def test_title_only_file_in_season_directory_is_not_guessed(
    tmp_path: Path,
):
    file = (
        tmp_path
        / "The Simpsons"
        / "Season 9"
        / "Bart Carny.m4v"
    )

    file.parent.mkdir(
        parents=True
    )
    file.touch()

    media = inspect_media(
        file
    )

    assert media.media_type == "movie"
    assert media.season is None
    assert media.episode is None
