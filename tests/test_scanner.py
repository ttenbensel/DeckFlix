from pathlib import Path

from deckflix_app.config import (
    DeckFlixConfig,
    DeckFlixPaths,
    NetworkPolicy,
)
from deckflix_app.inventory.models import (
    DriveRole,
    LibraryKind,
    MediaType,
)
from deckflix_app.inventory.scanner import InventoryScanner


def make_config(tmp_path: Path) -> DeckFlixConfig:
    library_root = tmp_path / "library"
    movie_library = library_root / "movie"
    tv_library = library_root / "tv"
    shuttle = tmp_path / "shuttle"
    logs = library_root / "deckflix-logs"

    movie_library.mkdir(parents=True)
    tv_library.mkdir(parents=True)
    shuttle.mkdir(parents=True)
    logs.mkdir(parents=True)

    return DeckFlixConfig(
        shuttle=shuttle,
        movie_libraries=(movie_library,),
        tv_libraries=(tv_library,),
        report_directory=logs,
        paths=DeckFlixPaths(
            quarantine=library_root / "deckflix-quarantine",
            repair_log=logs / "repair.log",
        ),
        read_only=False,
        operating_profile="normal",
        low_impact=False,
        network=NetworkPolicy(
            require_vpn=False,
            max_download_mbps=5,
            max_concurrent_downloads=1,
            allow_metadata_downloads=True,
            allow_jellyfin_refresh=True,
        ),
        source_path=tmp_path / "config.json",
    )


def test_scanner_builds_drive_inventory(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    inventory = InventoryScanner(config).build()

    assert len(inventory.drives) == 2

    library_drive = inventory.drives[0]
    shuttle_drive = inventory.drives[1]

    assert library_drive.id == "library-main"
    assert library_drive.role is DriveRole.LIBRARY
    assert library_drive.mount_point == config.movie_libraries[0].parent
    assert library_drive.online is True

    assert shuttle_drive.id == "shuttle-main"
    assert shuttle_drive.role is DriveRole.SHUTTLE
    assert shuttle_drive.mount_point == config.shuttle
    assert shuttle_drive.online is True


def test_scanner_builds_library_inventory(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    inventory = InventoryScanner(config).build()

    assert len(inventory.libraries) == 2

    movie_library = inventory.libraries[0]
    tv_library = inventory.libraries[1]

    assert movie_library.id == "movies-1"
    assert movie_library.name == "Movies"
    assert movie_library.kind is LibraryKind.MOVIES
    assert movie_library.drive_id == "library-main"
    assert movie_library.root == config.movie_libraries[0]

    assert tv_library.id == "tv-1"
    assert tv_library.name == "TV"
    assert tv_library.kind is LibraryKind.TV
    assert tv_library.drive_id == "library-main"
    assert tv_library.root == config.tv_libraries[0]


def test_scanner_marks_missing_shuttle_offline(
    tmp_path: Path,
) -> None:
    config = make_config(tmp_path)
    config.shuttle.rmdir()

    inventory = InventoryScanner(config).build()

    shuttle_drive = next(
        drive
        for drive in inventory.drives
        if drive.role is DriveRole.SHUTTLE
    )

    assert shuttle_drive.online is False


def test_scanner_discovers_movie_file(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    movie_file = (
        config.movie_libraries[0]
        / "Alien (1979)"
        / "Alien (1979).mkv"
    )
    movie_file.parent.mkdir(parents=True)
    movie_file.write_bytes(b"deckflix-movie")

    inventory = InventoryScanner(config).build()

    movies = [
        item
        for item in inventory.media
        if item.media_type is MediaType.MOVIE
    ]

    assert len(movies) == 1
    assert movies[0].title == "Alien (1979)"
    assert movies[0].files[0].path == movie_file
    assert movies[0].files[0].size == len(b"deckflix-movie")
    assert movies[0].files[0].library_id == "movies-1"
    assert movies[0].files[0].drive_id == "library-main"


def test_scanner_discovers_tv_episode(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    episode_file = (
        config.tv_libraries[0]
        / "Breaking Bad"
        / "Season 01"
        / "Breaking Bad - S01E01.mkv"
    )
    episode_file.parent.mkdir(parents=True)
    episode_file.write_bytes(b"deckflix-episode")

    inventory = InventoryScanner(config).build()

    episodes = [
        item
        for item in inventory.media
        if item.media_type is MediaType.EPISODE
    ]

    assert len(episodes) == 1
    assert episodes[0].title == "Breaking Bad - S01E01"
    assert episodes[0].files[0].path == episode_file
    assert episodes[0].files[0].library_id == "tv-1"


def test_scanner_ignores_non_video_files(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    movie_folder = (
        config.movie_libraries[0]
        / "Alien (1979)"
    )
    movie_folder.mkdir(parents=True)

    (movie_folder / "Alien (1979).mkv").write_bytes(b"video")
    (movie_folder / "poster.jpg").write_bytes(b"image")
    (movie_folder / "movie.nfo").write_text(
        "metadata",
        encoding="utf-8",
    )
    (movie_folder / "subtitle.srt").write_text(
        "subtitle",
        encoding="utf-8",
    )

    inventory = InventoryScanner(config).build()

    assert len(inventory.media) == 1
    assert inventory.media[0].files[0].path.name == "Alien (1979).mkv"


def test_scanner_records_scan_summary(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    first_file = config.movie_libraries[0] / "Movie One.mkv"
    second_file = config.tv_libraries[0] / "Show - S01E01.mp4"

    first_file.write_bytes(b"one")
    second_file.write_bytes(b"two")

    inventory = InventoryScanner(config).build()

    assert inventory.last_scan is not None
    assert inventory.last_scan.finished is not None
    assert inventory.last_scan.files_seen == 2
    assert inventory.last_scan.files_added == 2
    assert inventory.last_scan.files_removed == 0
    assert inventory.last_scan.files_updated == 0
    assert inventory.last_scan.errors == []


def test_scanner_media_ids_are_stable(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    movie_file = config.movie_libraries[0] / "Stable Movie.mkv"
    movie_file.write_bytes(b"stable")

    first_inventory = InventoryScanner(config).build()
    second_inventory = InventoryScanner(config).build()

    assert first_inventory.media[0].id == second_inventory.media[0].id
