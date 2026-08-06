from dataclasses import dataclass
from pathlib import Path
import json

from .checksum import file_checksum


@dataclass(slots=True)
class SnapshotEntry:
    path: Path
    size: int
    checksum: str


class MaintenanceSnapshot:

    def __init__(
        self,
        entries: list[SnapshotEntry],
    ):
        self.entries = entries


    @classmethod
    def create(
        cls,
        paths: list[Path],
    ):
        entries = []

        for path in paths:
            path = Path(path)

            if not path.exists():
                raise FileNotFoundError(
                    path
                )

            entries.append(
                SnapshotEntry(
                    path=path,
                    size=path.stat().st_size,
                    checksum=file_checksum(
                        path
                    ),
                )
            )

        return cls(
            entries
        )


    def verify(self) -> bool:
        for entry in self.entries:

            if not entry.path.exists():
                return False

            if (
                entry.path.stat().st_size
                != entry.size
            ):
                return False

            if (
                file_checksum(entry.path)
                != entry.checksum
            ):
                return False

        return True


    def save(
        self,
        path: Path,
    ):
        data = {
            "entries": [
                {
                    "path": str(entry.path),
                    "size": entry.size,
                    "checksum": entry.checksum,
                }
                for entry in self.entries
            ]
        }

        Path(path).write_text(
            json.dumps(
                data,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
