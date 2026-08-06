from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from datetime import datetime
import json

from .checksum import file_checksum


class JournalStatus(str, Enum):
    PENDING = "PENDING"
    MOVING = "MOVING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


@dataclass(slots=True)
class JournalEntry:
    source: Path
    destination: Path
    status: JournalStatus
    created_at: datetime

    source_size: int | None = None
    source_checksum: str | None = None

    destination_size: int | None = None
    destination_checksum: str | None = None

    completed_at: datetime | None = None
    error: str | None = None


class MaintenanceJournal:

    def __init__(
        self,
        path: Path,
    ):
        self.path = Path(path)
        self.entries: list[JournalEntry] = []


    def add(
        self,
        source: Path,
        destination: Path,
    ):
        source = Path(source)

        entry = JournalEntry(
            source=source,
            destination=Path(destination),
            status=JournalStatus.PENDING,
            created_at=datetime.now(),
        )

        if source.exists():
            entry.source_size = source.stat().st_size
            entry.source_checksum = file_checksum(
                source
            )

        self.entries.append(
            entry
        )


    def update(
        self,
        index: int,
        status: JournalStatus,
        error: str | None = None,
    ):
        entry = self.entries[index]

        entry.status = status
        entry.error = error

        if status is JournalStatus.VERIFIED:
            if entry.destination.exists():
                entry.destination_size = (
                    entry.destination.stat().st_size
                )

                entry.destination_checksum = (
                    file_checksum(
                        entry.destination
                    )
                )

            entry.completed_at = datetime.now()


    def save(self):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "entries": [
                {
                    "source": str(entry.source),
                    "destination": str(entry.destination),
                    "status": entry.status.value,

                    "source_size": entry.source_size,
                    "source_checksum": entry.source_checksum,

                    "destination_size": (
                        entry.destination_size
                    ),
                    "destination_checksum": (
                        entry.destination_checksum
                    ),

                    "created_at": (
                        entry.created_at.isoformat()
                    ),

                    "completed_at": (
                        entry.completed_at.isoformat()
                        if entry.completed_at
                        else None
                    ),

                    "error": entry.error,
                }
                for entry in self.entries
            ]
        }

        self.path.write_text(
            json.dumps(
                data,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    @classmethod
    def load(
        cls,
        path: Path,
    ):
        path = Path(path)

        journal = cls(
            path,
        )

        if not path.exists():
            return journal

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        for item in data.get(
            "entries",
            [],
        ):
            journal.entries.append(
                JournalEntry(
                    source=Path(
                        item["source"]
                    ),
                    destination=Path(
                        item["destination"]
                    ),
                    status=JournalStatus(
                        item["status"]
                    ),
                    created_at=datetime.fromisoformat(
                        item["created_at"]
                    ),
                    source_size=item.get(
                        "source_size"
                    ),
                    source_checksum=item.get(
                        "source_checksum"
                    ),
                    destination_size=item.get(
                        "destination_size"
                    ),
                    destination_checksum=item.get(
                        "destination_checksum"
                    ),
                    completed_at=(
                        datetime.fromisoformat(
                            item["completed_at"]
                        )
                        if item.get(
                            "completed_at"
                        )
                        else None
                    ),
                    error=item.get(
                        "error"
                    ),
                )
            )

        return journal
