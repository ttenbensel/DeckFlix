from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path

from .manager import OperationManager


@dataclass(frozen=True, slots=True)
class OperationHistoryRecord:
    operation_id: str
    created_at: str
    completed_at: str
    shuttle_path: str
    snapshot_files: int
    snapshot_bytes: int
    snapshot_fingerprint: str
    imported: int
    failed: int
    safe_to_empty: bool
    trust_score: int


def record_from_manager(
    manager: OperationManager,
    *,
    completed_at: datetime | None = None,
) -> OperationHistoryRecord:
    operation = manager.require_operation()

    if manager.import_result is None:
        raise ValueError(
            "Operation has no import result"
        )

    if manager.certificate is None:
        raise ValueError(
            "Operation has no certificate"
        )

    timestamp = completed_at or datetime.now()

    return OperationHistoryRecord(
        operation_id=operation.id,
        created_at=operation.created_at.isoformat(),
        completed_at=timestamp.isoformat(),
        shuttle_path=str(
            operation.snapshot.shuttle_path
        ),
        snapshot_files=(
            operation.snapshot.file_count
        ),
        snapshot_bytes=(
            operation.snapshot.total_bytes
        ),
        snapshot_fingerprint=(
            operation.snapshot.fingerprint
        ),
        imported=manager.import_result.completed,
        failed=manager.import_result.failed,
        safe_to_empty=(
            manager.certificate.safety.safe
        ),
        trust_score=manager.certificate.trust_score,
    )


def save_history_record(
    record: OperationHistoryRecord,
    history_directory: Path,
) -> Path:
    history_directory = Path(history_directory)

    history_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        history_directory
        / f"{record.operation_id}.json"
    )

    temporary = destination.with_suffix(
        ".json.tmp"
    )

    temporary.write_text(
        json.dumps(
            asdict(record),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(destination)

    return destination


def load_history_record(
    path: Path,
) -> OperationHistoryRecord:
    data = json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )

    return OperationHistoryRecord(**data)


def list_history_records(
    history_directory: Path,
) -> list[OperationHistoryRecord]:
    history_directory = Path(
        history_directory
    )

    if not history_directory.exists():
        return []

    records = []

    for path in history_directory.glob(
        "DF-*.json"
    ):
        try:
            records.append(
                load_history_record(path)
            )
        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
        ):
            continue

    return sorted(
        records,
        key=lambda record: record.completed_at,
        reverse=True,
    )


@dataclass(frozen=True, slots=True)
class RepairHistoryEntry:
    source: str
    destination: str
    action: str
    reason: str
    source_size: int
    source_modified_ns: int
    source_checksum: str
    status: str
    destination_checksum: str | None
    completed_at: str | None
    error: str | None


@dataclass(frozen=True, slots=True)
class RepairOperationHistoryRecord:
    operation_id: str
    created_at: str
    updated_at: str
    state: str
    write_authorized: bool
    plan_fingerprint: str
    entries: int
    verified: int
    failed: int
    pending: int
    copying: int
    total_bytes: int
    destinations: tuple[str, ...]
    entries_detail: tuple[
        RepairHistoryEntry,
        ...
    ]
    path: str


def load_repair_history_record(
    path: Path,
) -> RepairOperationHistoryRecord:
    path = Path(path)

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    entries = data.get(
        "entries",
        [],
    )

    statuses = {
        "VERIFIED": 0,
        "FAILED": 0,
        "PENDING": 0,
        "COPYING": 0,
    }

    total_bytes = 0
    destinations: list[str] = []
    entry_details: list[
        RepairHistoryEntry
    ] = []

    for entry in entries:
        status = str(
            entry.get(
                "status",
                "",
            )
        )

        if status in statuses:
            statuses[status] += 1

        try:
            total_bytes += int(
                entry.get(
                    "source_size",
                    0,
                )
                or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

        destination = entry.get(
            "destination"
        )

        if destination:
            destinations.append(
                str(destination)
            )

        entry_details.append(
            RepairHistoryEntry(
                source=str(
                    entry.get(
                        "source",
                        "",
                    )
                ),
                destination=str(
                    entry.get(
                        "destination",
                        "",
                    )
                ),
                action=str(
                    entry.get(
                        "action",
                        "",
                    )
                ),
                reason=str(
                    entry.get(
                        "reason",
                        "",
                    )
                ),
                source_size=int(
                    entry.get(
                        "source_size",
                        0,
                    )
                    or 0
                ),
                source_modified_ns=int(
                    entry.get(
                        "source_modified_ns",
                        0,
                    )
                    or 0
                ),
                source_checksum=str(
                    entry.get(
                        "source_checksum",
                        "",
                    )
                ),
                status=str(
                    entry.get(
                        "status",
                        "",
                    )
                ),
                destination_checksum=(
                    str(
                        entry.get(
                            "destination_checksum"
                        )
                    )
                    if entry.get(
                        "destination_checksum"
                    )
                    else None
                ),
                completed_at=(
                    str(
                        entry.get(
                            "completed_at"
                        )
                    )
                    if entry.get(
                        "completed_at"
                    )
                    else None
                ),
                error=(
                    str(
                        entry.get(
                            "error"
                        )
                    )
                    if entry.get(
                        "error"
                    )
                    else None
                ),
            )
        )

    return RepairOperationHistoryRecord(
        operation_id=str(
            data["operation_id"]
        ),
        created_at=str(
            data["created_at"]
        ),
        updated_at=str(
            data["updated_at"]
        ),
        state=str(
            data["state"]
        ),
        write_authorized=bool(
            data.get(
                "write_authorized",
                False,
            )
        ),
        plan_fingerprint=str(
            data.get(
                "plan_fingerprint",
                "",
            )
        ),
        entries=len(entries),
        verified=statuses["VERIFIED"],
        failed=statuses["FAILED"],
        pending=statuses["PENDING"],
        copying=statuses["COPYING"],
        total_bytes=total_bytes,
        destinations=tuple(
            destinations
        ),
        entries_detail=tuple(
            entry_details
        ),
        path=str(path),
    )


def list_repair_history_records(
    history_directory: Path,
) -> list[
    RepairOperationHistoryRecord
]:
    history_directory = Path(
        history_directory
    )

    if not history_directory.exists():
        return []

    records = []

    for path in history_directory.glob(
        "DR-*.json"
    ):
        try:
            records.append(
                load_repair_history_record(
                    path
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

    return sorted(
        records,
        key=lambda record: record.updated_at,
        reverse=True,
    )
