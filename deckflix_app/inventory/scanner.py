"""Filesystem inventory scanner for DeckFlix."""

from __future__ import annotations

import hashlib
from pathlib import Path

from deckflix_app.config import DeckFlixConfig
from deckflix_app.inventory.models import (
    Drive,
    DriveRole,
    Inventory,
    Library,
    LibraryKind,
    MediaFile,
    MediaItem,
    MediaType,
    ScanRecord,
    utc_now,
)


VIDEO_EXTENSIONS = {
    ".3gp",
    ".avi",
    ".divx",
    ".flv",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".mts",
    ".ogm",
    ".ogv",
    ".ts",
    ".vob",
    ".webm",
    ".wmv",
}


class InventoryScanner:
    """Build an inventory from configured DeckFlix storage paths."""

    def __init__(self, config: DeckFlixConfig) -> None:
        self.config = config

    def build(self) -> Inventory:
        """Scan configured libraries and return a new inventory."""
        scan = ScanRecord(started=utc_now())
        inventory = Inventory.empty()

        inventory.drives.extend(self._discover_drives())
        inventory.libraries.extend(self._discover_libraries())
        inventory.media.extend(
            self._discover_media(
                libraries=inventory.libraries,
                scan=scan,
            )
        )

        scan.files_seen = sum(
            len(item.files)
            for item in inventory.media
        )
        scan.files_added = scan.files_seen
        scan.finished = utc_now()

        inventory.last_scan = scan
        inventory.updated = scan.finished

        return inventory

    def _discover_drives(self) -> list[Drive]:
        """Create inventory drive records from the current configuration."""
        library_mount = self._library_mount_point()

        return [
            Drive(
                id="library-main",
                label="Main Library",
                role=DriveRole.LIBRARY,
                mount_point=library_mount,
                online=library_mount.exists(),
            ),
            Drive(
                id="shuttle-main",
                label="Media Shuttle",
                role=DriveRole.SHUTTLE,
                mount_point=self.config.shuttle,
                online=self.config.shuttle.exists(),
            ),
        ]

    def _discover_libraries(self) -> list[Library]:
        """Create movie and television library records."""
        libraries: list[Library] = []

        for index, path in enumerate(
            self.config.movie_libraries,
            start=1,
        ):
            libraries.append(
                Library(
                    id=f"movies-{index}",
                    name=(
                        "Movies"
                        if len(self.config.movie_libraries) == 1
                        else f"Movies {index}"
                    ),
                    kind=LibraryKind.MOVIES,
                    drive_id="library-main",
                    root=path,
                )
            )

        for index, path in enumerate(
            self.config.tv_libraries,
            start=1,
        ):
            libraries.append(
                Library(
                    id=f"tv-{index}",
                    name=(
                        "TV"
                        if len(self.config.tv_libraries) == 1
                        else f"TV {index}"
                    ),
                    kind=LibraryKind.TV,
                    drive_id="library-main",
                    root=path,
                )
            )

        return libraries

    def _discover_media(
        self,
        libraries: list[Library],
        scan: ScanRecord,
    ) -> list[MediaItem]:
        """Discover video files in every configured library."""
        media: list[MediaItem] = []

        for library in libraries:
            media.extend(
                self._scan_library(
                    library=library,
                    scan=scan,
                )
            )

        return media

    def _scan_library(
        self,
        library: Library,
        scan: ScanRecord,
    ) -> list[MediaItem]:
        """Discover video files beneath one library root."""
        if not library.root.exists():
            scan.errors.append(
                f"Library path does not exist: {library.root}"
            )
            return []

        if not library.root.is_dir():
            scan.errors.append(
                f"Library path is not a directory: {library.root}"
            )
            return []

        discovered: list[MediaItem] = []

        try:
            candidates = sorted(
                path
                for path in library.root.rglob("*")
                if path.is_file() and self._is_video_file(path)
            )
        except OSError as exc:
            scan.errors.append(
                f"Unable to scan library {library.root}: {exc}"
            )
            return []

        for path in candidates:
            item = self._build_media_item(
                path=path,
                library=library,
                scan=scan,
            )

            if item is not None:
                discovered.append(item)

        return discovered

    def _build_media_item(
        self,
        path: Path,
        library: Library,
        scan: ScanRecord,
    ) -> MediaItem | None:
        """Create an inventory record for one discovered media file."""
        try:
            file_size = path.stat().st_size
        except OSError as exc:
            scan.errors.append(
                f"Unable to inspect file {path}: {exc}"
            )
            return None

        now = utc_now()
        relative_path = path.relative_to(library.root)

        media_file = MediaFile(
            path=path,
            drive_id=library.drive_id,
            library_id=library.id,
            size=file_size,
            added=now,
            last_seen=now,
        )

        media_type = (
            MediaType.MOVIE
            if library.kind is LibraryKind.MOVIES
            else MediaType.EPISODE
        )

        return MediaItem(
            id=self._stable_media_id(
                library_id=library.id,
                relative_path=relative_path,
            ),
            media_type=media_type,
            title=path.stem,
            files=[media_file],
        )

    @staticmethod
    def _is_video_file(path: Path) -> bool:
        """Return whether a path has a supported video extension."""
        return path.suffix.lower() in VIDEO_EXTENSIONS

    @staticmethod
    def _stable_media_id(
        library_id: str,
        relative_path: Path,
    ) -> str:
        """Create a stable ID from library identity and relative path."""
        identity = (
            f"{library_id}:"
            f"{relative_path.as_posix().casefold()}"
        )

        digest = hashlib.sha256(
            identity.encode("utf-8")
        ).hexdigest()[:20]

        return f"file-{digest}"

    def _library_mount_point(self) -> Path:
        """Return the common parent used for primary media libraries."""
        configured_libraries = [
            *self.config.movie_libraries,
            *self.config.tv_libraries,
        ]

        if not configured_libraries:
            raise ValueError(
                "At least one movie or TV library must be configured"
            )

        return configured_libraries[0].parent
