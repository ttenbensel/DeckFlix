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
        raise ValueError("Operation has no import result")

    if manager.certificate is None:
        raise ValueError("Operation has no certificate")

    timestamp = completed_at or datetime.now()

    return OperationHistoryRecord(
        operation_id=operation.id,
        created_at=operation.created_at.isoformat(),
        completed_at=timestamp.isoformat(),
        shuttle_path=str(operation.snapshot.shuttle_path),
        snapshot_files=operation.snapshot.file_count,
        snapshot_bytes=operation.snapshot.total_bytes,
        snapshot_fingerprint=operation.snapshot.fingerprint,
        imported=manager.import_result.completed,
        failed=manager.import_result.failed,
        safe_to_empty=manager.certificate.safety.safe,
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

    temporary = destination.with_suffix(".json.tmp")

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
        Path(path).read_text(encoding="utf-8")
    )

    return OperationHistoryRecord(**data)


def list_history_records(
    history_directory: Path,
) -> list[OperationHistoryRecord]:
    history_directory = Path(history_directory)

    if not history_directory.exists():
        return []

    records = []

    for path in history_directory.glob("DF-*.json"):
        try:
            records.append(load_history_record(path))
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
