from datetime import datetime, timezone
from pathlib import Path

import pytest

from deckflix_app.inventory import (
    Drive,
    DriveRole,
    Inventory,
    InventoryRepository,
    Library,
    LibraryKind,
    MediaFile,
    MediaItem,
    MediaType,
    ScanRecord,
)


def test_empty_inventory_round_trip(tmp_path: Path) -> None:
    repository = InventoryRepository(tmp_path / "inventory.json")
    inventory = Inventory.empty()

    repository.save(inventory)
    loaded = repository.load()

    assert loaded.schema == 1
    assert loaded.drives == []
    assert loaded.libraries == []
    assert loaded.media == []
    assert loaded.last_scan is None


def test_complete_inventory_round_trip(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)

    drive = Drive(
        id="library-4tb-01",
        label="Main Media",
        role=DriveRole.LIBRARY,
        serial="SERIAL-123",
        uuid="UUID-123",
        mount_point=Path("/data/library1"),
        capacity=4_000_000_000_000,
        free_space=1_000_000_000_000,
        online=True,
        last_seen=now,
    )

    library = Library(
        id="movies-main",
        name="Main Movies",
        kind=LibraryKind.MOVIES,
        drive_id=drive.id,
        root=Path("/data/library1/movies"),
    )

    media_file = MediaFile(
        path=Path("/data/library1/movies/Alien (1979)/Alien.mkv"),
        drive_id=drive.id,
        library_id=library.id,
        size=123456789,
        checksum="abc123",
        codec="hevc",
        resolution="2160p",
        audio="truehd",
        subtitles=["eng"],
        added=now,
        last_seen=now,
    )

    movie = MediaItem(
        id="movie-alien-1979",
        media_type=MediaType.MOVIE,
        title="Alien",
        year=1979,
        files=[media_file],
    )

    scan = ScanRecord(
        started=now,
        finished=now,
        files_seen=1,
        files_added=1,
    )

    inventory = Inventory(
        drives=[drive],
        libraries=[library],
        media=[movie],
        last_scan=scan,
    )

    repository = InventoryRepository(tmp_path / "inventory.json")
    repository.save(inventory)

    loaded = repository.load()

    assert loaded.drives[0].role is DriveRole.LIBRARY
    assert loaded.libraries[0].kind is LibraryKind.MOVIES
    assert loaded.media[0].media_type is MediaType.MOVIE
    assert loaded.media[0].files[0].path == media_file.path
    assert loaded.media[0].files[0].checksum == "abc123"
    assert loaded.last_scan is not None
    assert loaded.last_scan.files_seen == 1


def test_missing_inventory_returns_empty_inventory(tmp_path: Path) -> None:
    repository = InventoryRepository(tmp_path / "missing.json")

    inventory = repository.load()

    assert inventory.schema == 1
    assert inventory.media == []


def test_repository_creates_backup(tmp_path: Path) -> None:
    repository = InventoryRepository(tmp_path / "inventory.json")
    repository.save(Inventory.empty())

    backup_file = repository.backup()

    assert backup_file is not None
    assert backup_file.exists()
    assert backup_file.parent == tmp_path / "backups"


def test_repository_rejects_unknown_schema(tmp_path: Path) -> None:
    inventory_file = tmp_path / "inventory.json"
    inventory_file.write_text(
        """
        {
          "schema": 999,
          "created": "2026-01-01T00:00:00+00:00",
          "updated": "2026-01-01T00:00:00+00:00",
          "drives": [],
          "libraries": [],
          "media": [],
          "last_scan": null
        }
        """,
        encoding="utf-8",
    )

    repository = InventoryRepository(inventory_file)

    with pytest.raises(ValueError, match="Unsupported inventory schema"):
        repository.load()
