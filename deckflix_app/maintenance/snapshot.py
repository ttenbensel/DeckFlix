from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SnapshotEntry:
    path: Path
    size: int
    modified_time: float


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

            stat = path.stat()

            entries.append(
                SnapshotEntry(
                    path=path,
                    size=stat.st_size,
                    modified_time=stat.st_mtime,
                )
            )

        return cls(
            entries
        )

    def verify(self) -> bool:
        for entry in self.entries:

            if not entry.path.exists():
                return False

            stat = entry.path.stat()

            if stat.st_size != entry.size:
                return False

            if stat.st_mtime != entry.modified_time:
                return False

        return True
