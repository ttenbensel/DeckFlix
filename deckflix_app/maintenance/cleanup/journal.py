from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from datetime import datetime
import json


class CleanupStatus(str, Enum):
    PENDING = "PENDING"
    REMOVING = "REMOVING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


@dataclass(slots=True)
class CleanupJournalEntry:
    path: Path
    action: str
    reason: str
    status: CleanupStatus
    created_at: datetime

    completed_at: datetime | None = None
    error: str | None = None


class CleanupJournal:

    def __init__(
        self,
        path: Path,
    ):
        self.path = Path(path)
        self.entries: list[CleanupJournalEntry] = []


    def add(
        self,
        action: str,
        path: Path,
        reason: str,
    ):

        self.entries.append(
            CleanupJournalEntry(
                path=Path(path),
                action=action,
                reason=reason,
                status=CleanupStatus.PENDING,
                created_at=datetime.now(),
            )
        )


    def update(
        self,
        index: int,
        status: CleanupStatus,
        error: str | None = None,
    ):

        entry = self.entries[index]

        entry.status = status
        entry.error = error

        if status is CleanupStatus.VERIFIED:
            entry.completed_at = datetime.now()


    def save(self):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "entries": [
                {
                    "path": str(entry.path),
                    "action": entry.action,
                    "reason": entry.reason,
                    "status": entry.status.value,

                    "created_at":
                        entry.created_at.isoformat(),

                    "completed_at":
                        (
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
                CleanupJournalEntry(
                    path=Path(
                        item["path"]
                    ),
                    action=item["action"],
                    reason=item["reason"],
                    status=CleanupStatus(
                        item["status"]
                    ),
                    created_at=datetime.fromisoformat(
                        item["created_at"]
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
