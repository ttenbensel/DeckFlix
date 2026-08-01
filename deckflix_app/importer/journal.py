from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from .models import ImportJob


class JournalStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(slots=True)
class JournalEntry:
    source: str
    destination: str
    status: JournalStatus = JournalStatus.PENDING
    error: str = ""
    completed_at: str | None = None


@dataclass(slots=True)
class ImportJournal:
    operation_id: str
    created_at: str
    updated_at: str
    entries: dict[str, JournalEntry] = field(default_factory=dict)

    @property
    def completed(self) -> int:
        return sum(
            1
            for entry in self.entries.values()
            if entry.status is JournalStatus.COMPLETED
        )

    @property
    def failed(self) -> int:
        return sum(
            1
            for entry in self.entries.values()
            if entry.status is JournalStatus.FAILED
        )

    @property
    def pending(self) -> int:
        return sum(
            1
            for entry in self.entries.values()
            if entry.status is JournalStatus.PENDING
        )


def job_key(job: ImportJob) -> str:
    return str(Path(job.destination).resolve())


def create_import_journal(
    operation_id: str,
    jobs: list[ImportJob],
) -> ImportJournal:
    timestamp = datetime.now().isoformat()

    return ImportJournal(
        operation_id=operation_id,
        created_at=timestamp,
        updated_at=timestamp,
        entries={
            job_key(job): JournalEntry(
                source=str(Path(job.source).resolve()),
                destination=str(
                    Path(job.destination).resolve()
                ),
            )
            for job in jobs
        },
    )


def save_import_journal(
    journal: ImportJournal,
    destination: Path,
) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    journal.updated_at = datetime.now().isoformat()

    data = {
        "operation_id": journal.operation_id,
        "created_at": journal.created_at,
        "updated_at": journal.updated_at,
        "entries": {
            key: {
                **asdict(entry),
                "status": entry.status.value,
            }
            for key, entry in journal.entries.items()
        },
    }

    temporary = destination.with_suffix(
        destination.suffix + ".tmp"
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

    temporary.replace(destination)

    return destination


def load_import_journal(
    source: Path,
) -> ImportJournal | None:
    source = Path(source)

    if not source.exists():
        return None

    data = json.loads(
        source.read_text(encoding="utf-8")
    )

    return ImportJournal(
        operation_id=data["operation_id"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        entries={
            key: JournalEntry(
                source=value["source"],
                destination=value["destination"],
                status=JournalStatus(value["status"]),
                error=value.get("error", ""),
                completed_at=value.get("completed_at"),
            )
            for key, value in data["entries"].items()
        },
    )


def get_or_create_import_journal(
    *,
    operation_id: str,
    jobs: list[ImportJob],
    journal_path: Path,
) -> ImportJournal:
    journal = load_import_journal(journal_path)

    if journal is None:
        journal = create_import_journal(
            operation_id,
            jobs,
        )
        save_import_journal(
            journal,
            journal_path,
        )
        return journal

    if journal.operation_id != operation_id:
        raise ValueError(
            "Import journal belongs to another operation: "
            f"{journal.operation_id}"
        )

    for job in jobs:
        key = job_key(job)

        if key not in journal.entries:
            journal.entries[key] = JournalEntry(
                source=str(Path(job.source).resolve()),
                destination=str(
                    Path(job.destination).resolve()
                ),
            )

    save_import_journal(
        journal,
        journal_path,
    )

    return journal


def mark_journal_completed(
    journal: ImportJournal,
    job: ImportJob,
) -> None:
    entry = journal.entries[job_key(job)]
    entry.status = JournalStatus.COMPLETED
    entry.error = ""
    entry.completed_at = datetime.now().isoformat()


def mark_journal_failed(
    journal: ImportJournal,
    job: ImportJob,
    error: Exception | str,
) -> None:
    entry = journal.entries[job_key(job)]
    entry.status = JournalStatus.FAILED
    entry.error = str(error)
    entry.completed_at = None


def mark_journal_pending(
    journal: ImportJournal,
    job: ImportJob,
) -> None:
    entry = journal.entries[job_key(job)]
    entry.status = JournalStatus.PENDING
    entry.error = ""
    entry.completed_at = None


def delete_import_journal(path: Path) -> None:
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
