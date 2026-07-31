"""Core data models for the DeckFlix inventory index."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


INVENTORY_SCHEMA_VERSION = 1


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def datetime_to_string(value: datetime) -> str:
    """Serialize a datetime using ISO 8601."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()


def datetime_from_string(value: str) -> datetime:
    """Deserialize an ISO-8601 datetime."""
    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


class DriveRole(str, Enum):
    LIBRARY = "library"
    SHUTTLE = "shuttle"
    BACKUP = "backup"
    EXTERNAL = "external"


class LibraryKind(str, Enum):
    MOVIES = "movies"
    TV = "tv"


class MediaType(str, Enum):
    MOVIE = "movie"
    EPISODE = "episode"


@dataclass
class Drive:
    """A physical or logical storage device known to DeckFlix."""

    id: str
    label: str
    role: DriveRole
    mount_point: Path

    serial: str | None = None
    uuid: str | None = None

    capacity: int = 0
    free_space: int = 0

    online: bool = True
    last_seen: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "role": self.role.value,
            "serial": self.serial,
            "uuid": self.uuid,
            "mount_point": str(self.mount_point),
            "capacity": self.capacity,
            "free_space": self.free_space,
            "online": self.online,
            "last_seen": datetime_to_string(self.last_seen),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Drive:
        return cls(
            id=data["id"],
            label=data["label"],
            role=DriveRole(data["role"]),
            serial=data.get("serial"),
            uuid=data.get("uuid"),
            mount_point=Path(data["mount_point"]),
            capacity=int(data.get("capacity", 0)),
            free_space=int(data.get("free_space", 0)),
            online=bool(data.get("online", True)),
            last_seen=datetime_from_string(data["last_seen"]),
        )


@dataclass
class Library:
    """A configured movie or television library."""

    id: str
    name: str
    kind: LibraryKind
    drive_id: str
    root: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind.value,
            "drive_id": self.drive_id,
            "root": str(self.root),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Library:
        return cls(
            id=data["id"],
            name=data["name"],
            kind=LibraryKind(data["kind"]),
            drive_id=data["drive_id"],
            root=Path(data["root"]),
        )


@dataclass
class MediaFile:
    """One physical media file stored on a DeckFlix-managed drive."""

    path: Path
    drive_id: str
    library_id: str
    size: int

    checksum: str | None = None
    codec: str | None = None
    resolution: str | None = None
    audio: str | None = None
    subtitles: list[str] = field(default_factory=list)

    added: datetime = field(default_factory=utc_now)
    last_seen: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "drive_id": self.drive_id,
            "library_id": self.library_id,
            "size": self.size,
            "checksum": self.checksum,
            "codec": self.codec,
            "resolution": self.resolution,
            "audio": self.audio,
            "subtitles": list(self.subtitles),
            "added": datetime_to_string(self.added),
            "last_seen": datetime_to_string(self.last_seen),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MediaFile:
        return cls(
            path=Path(data["path"]),
            drive_id=data["drive_id"],
            library_id=data["library_id"],
            size=int(data["size"]),
            checksum=data.get("checksum"),
            codec=data.get("codec"),
            resolution=data.get("resolution"),
            audio=data.get("audio"),
            subtitles=list(data.get("subtitles", [])),
            added=datetime_from_string(data["added"]),
            last_seen=datetime_from_string(data["last_seen"]),
        )


@dataclass
class MediaItem:
    """A movie or television episode and all known versions of it."""

    id: str
    media_type: MediaType
    title: str
    year: int | None = None
    files: list[MediaFile] = field(default_factory=list)

    series_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "media_type": self.media_type.value,
            "title": self.title,
            "year": self.year,
            "series_title": self.series_title,
            "season_number": self.season_number,
            "episode_number": self.episode_number,
            "files": [media_file.to_dict() for media_file in self.files],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MediaItem:
        return cls(
            id=data["id"],
            media_type=MediaType(data["media_type"]),
            title=data["title"],
            year=data.get("year"),
            series_title=data.get("series_title"),
            season_number=data.get("season_number"),
            episode_number=data.get("episode_number"),
            files=[
                MediaFile.from_dict(file_data)
                for file_data in data.get("files", [])
            ],
        )


@dataclass
class ScanRecord:
    """Summary of one inventory scan."""

    started: datetime
    finished: datetime | None = None

    files_seen: int = 0
    files_added: int = 0
    files_removed: int = 0
    files_updated: int = 0

    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "started": datetime_to_string(self.started),
            "finished": (
                datetime_to_string(self.finished)
                if self.finished is not None
                else None
            ),
            "files_seen": self.files_seen,
            "files_added": self.files_added,
            "files_removed": self.files_removed,
            "files_updated": self.files_updated,
            "errors": list(self.errors),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScanRecord:
        finished = data.get("finished")

        return cls(
            started=datetime_from_string(data["started"]),
            finished=(
                datetime_from_string(finished)
                if finished is not None
                else None
            ),
            files_seen=int(data.get("files_seen", 0)),
            files_added=int(data.get("files_added", 0)),
            files_removed=int(data.get("files_removed", 0)),
            files_updated=int(data.get("files_updated", 0)),
            errors=list(data.get("errors", [])),
        )


@dataclass
class Inventory:
    """The complete DeckFlix media and storage inventory."""

    schema: int = INVENTORY_SCHEMA_VERSION
    created: datetime = field(default_factory=utc_now)
    updated: datetime = field(default_factory=utc_now)

    drives: list[Drive] = field(default_factory=list)
    libraries: list[Library] = field(default_factory=list)
    media: list[MediaItem] = field(default_factory=list)

    last_scan: ScanRecord | None = None

    @classmethod
    def empty(cls) -> Inventory:
        """Create an empty inventory using the current schema."""
        now = utc_now()

        return cls(
            schema=INVENTORY_SCHEMA_VERSION,
            created=now,
            updated=now,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "created": datetime_to_string(self.created),
            "updated": datetime_to_string(self.updated),
            "drives": [drive.to_dict() for drive in self.drives],
            "libraries": [library.to_dict() for library in self.libraries],
            "media": [item.to_dict() for item in self.media],
            "last_scan": (
                self.last_scan.to_dict()
                if self.last_scan is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Inventory:
        schema = int(data["schema"])

        if schema != INVENTORY_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported inventory schema "
                f"{schema}; expected {INVENTORY_SCHEMA_VERSION}"
            )

        last_scan_data = data.get("last_scan")

        return cls(
            schema=schema,
            created=datetime_from_string(data["created"]),
            updated=datetime_from_string(data["updated"]),
            drives=[
                Drive.from_dict(drive_data)
                for drive_data in data.get("drives", [])
            ],
            libraries=[
                Library.from_dict(library_data)
                for library_data in data.get("libraries", [])
            ],
            media=[
                MediaItem.from_dict(item_data)
                for item_data in data.get("media", [])
            ],
            last_scan=(
                ScanRecord.from_dict(last_scan_data)
                if last_scan_data is not None
                else None
            ),
        )
