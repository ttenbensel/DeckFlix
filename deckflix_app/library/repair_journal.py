from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import shutil


class RepairJournalStatus(str, Enum):
    PENDING = "PENDING"
    COPYING = "COPYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


@dataclass(slots=True)
class RepairJournalEntry:
    source: Path
    destination: Path
    action: str
    reason: str

    source_size: int
    source_modified_ns: int
    source_checksum: str

    status: RepairJournalStatus = RepairJournalStatus.PENDING

    destination_checksum: str | None = None
    completed_at: datetime | None = None
    error: str | None = None


class LibraryRepairJournal:
    """
    Persistent journal for one DeckFlix library repair operation.

    This class only persists repair state.
    It does not modify media files.

    Terminal repair journals are historical records and must
    never be reused as the active operation for a new repair
    plan.
    """

    VERSION = 1

    TERMINAL_STATES = {
        "COMPLETE",
        "FAILED",
        "INVALIDATED",
    }

    def __init__(
        self,
        path: Path,
        *,
        operation_id: str,
    ) -> None:
        self.path = Path(path)
        self.operation_id = operation_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.entries: list[RepairJournalEntry] = []

        self.state = "CREATED"
        self.write_authorized = False
        self.plan_fingerprint = ""

    @property
    def all_entries_verified(self) -> bool:
        return bool(self.entries) and all(
            entry.status is RepairJournalStatus.VERIFIED
            for entry in self.entries
        )

    def save(self) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.updated_at = datetime.now()

        data = {
            "version": self.VERSION,
            "operation_id": self.operation_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "state": self.state,
            "write_authorized": self.write_authorized,
            "plan_fingerprint": self.plan_fingerprint,
            "entries": [
                {
                    "source": str(entry.source),
                    "destination": str(entry.destination),
                    "action": entry.action,
                    "reason": entry.reason,
                    "source_size": entry.source_size,
                    "source_modified_ns": (
                        entry.source_modified_ns
                    ),
                    "source_checksum": (
                        entry.source_checksum
                    ),
                    "status": entry.status.value,
                    "destination_checksum": (
                        entry.destination_checksum
                    ),
                    "completed_at": (
                        entry.completed_at.isoformat()
                        if entry.completed_at
                        else None
                    ),
                    "error": entry.error,
                }
                for entry in self.entries
            ],
        }

        temporary = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        temporary.write_text(
            json.dumps(
                data,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        temporary.replace(self.path)

    def _archive_terminal_journal(self) -> Path:
        history_directory = (
            self.path.parent
            / "repair-history"
        )

        history_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        archive_path = (
            history_directory
            / f"{self.operation_id}.json"
        )

        if archive_path.exists():
            raise RuntimeError(
                "Repair history already contains "
                f"operation {self.operation_id}."
            )

        shutil.move(
            str(self.path),
            str(archive_path),
        )

        return archive_path

    def archive_terminal(
        self,
        *,
        recover_verified: bool = True,
    ) -> Path:
        """
        Archive this terminal operation.

        A terminal operation is never reused as the active
        operation. If the journal is INVALIDATED but every
        journal entry is VERIFIED, recover the persisted state
        to COMPLETE before archiving it.

        This only moves the journal metadata file. It never
        modifies media files.
        """

        if self.state not in self.TERMINAL_STATES:
            raise ValueError(
                "Only terminal repair journals can be archived."
            )

        if (
            recover_verified
            and self.state == "INVALIDATED"
            and self.all_entries_verified
        ):
            self.state = "COMPLETE"
            self.write_authorized = False

            self.save()

        return self._archive_terminal_journal()

    @classmethod
    def load(
        cls,
        path: Path,
    ) -> LibraryRepairJournal | None:
        """
        Load the active repair journal.

        Terminal journals are never returned as active journals.
        They are archived so the next RepairOperationManager gets
        a fresh operation.

        This method does not modify media files.
        """

        path = Path(path)

        if not path.exists():
            return None

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if int(data.get("version", 0)) != cls.VERSION:
            raise ValueError(
                "Unsupported library repair journal version."
            )

        journal = cls(
            path,
            operation_id=data["operation_id"],
        )

        journal.created_at = datetime.fromisoformat(
            data["created_at"]
        )

        journal.updated_at = datetime.fromisoformat(
            data["updated_at"]
        )

        journal.state = data["state"]
        journal.write_authorized = bool(
            data.get(
                "write_authorized",
                False,
            )
        )

        journal.plan_fingerprint = data.get(
            "plan_fingerprint",
            "",
        )

        for item in data.get(
            "entries",
            [],
        ):
            journal.entries.append(
                RepairJournalEntry(
                    source=Path(
                        item["source"]
                    ),
                    destination=Path(
                        item["destination"]
                    ),
                    action=item["action"],
                    reason=item["reason"],
                    source_size=int(
                        item["source_size"]
                    ),
                    source_modified_ns=int(
                        item["source_modified_ns"]
                    ),
                    source_checksum=item[
                        "source_checksum"
                    ],
                    status=RepairJournalStatus(
                        item["status"]
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
                    error=item.get("error"),
                )
            )

        if journal.state in cls.TERMINAL_STATES:
            journal.archive_terminal()

            return None

        return journal
