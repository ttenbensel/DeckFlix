from datetime import datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from deckflix_app.scanner import scan_videos

from .models import (
    Operation,
    OperationState,
    ShuttleSnapshot,
    SnapshotFile,
)


def _snapshot_files(shuttle_path: Path) -> tuple[SnapshotFile, ...]:
    entries = []

    for file in scan_videos(shuttle_path):
        stat = file.stat()

        entries.append(
            SnapshotFile(
                relative_path=file.relative_to(shuttle_path),
                size=stat.st_size,
                modified_ns=stat.st_mtime_ns,
            )
        )

    return tuple(
        sorted(
            entries,
            key=lambda item: item.relative_path.as_posix().casefold(),
        )
    )


def snapshot_fingerprint(
    files: tuple[SnapshotFile, ...],
) -> str:
    digest = sha256()

    for item in files:
        digest.update(item.relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item.size).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(item.modified_ns).encode("ascii"))
        digest.update(b"\n")

    return digest.hexdigest()


def create_shuttle_snapshot(
    shuttle_path: Path,
    *,
    created_at: datetime | None = None,
) -> ShuttleSnapshot:
    shuttle_path = Path(shuttle_path).resolve()

    if not shuttle_path.exists():
        raise FileNotFoundError(
            f"Shuttle path does not exist: {shuttle_path}"
        )

    if not shuttle_path.is_dir():
        raise NotADirectoryError(
            f"Shuttle path is not a directory: {shuttle_path}"
        )

    files = _snapshot_files(shuttle_path)
    timestamp = created_at or datetime.now()

    return ShuttleSnapshot(
        shuttle_path=shuttle_path,
        device_id=shuttle_path.stat().st_dev,
        files=files,
        total_bytes=sum(item.size for item in files),
        fingerprint=snapshot_fingerprint(files),
        created_at=timestamp,
    )


def create_operation(
    shuttle_path: Path,
    *,
    created_at: datetime | None = None,
    operation_id: str | None = None,
) -> Operation:
    timestamp = created_at or datetime.now()
    snapshot = create_shuttle_snapshot(
        shuttle_path,
        created_at=timestamp,
    )

    generated_id = operation_id or (
        f"DF-{timestamp.strftime('%Y%m%d-%H%M%S')}-"
        f"{uuid4().hex[:6].upper()}"
    )

    return Operation(
        id=generated_id,
        state=OperationState.SNAPSHOT_READY,
        snapshot=snapshot,
        created_at=timestamp,
    )


def snapshot_matches_current(
    snapshot: ShuttleSnapshot,
) -> bool:
    path = snapshot.shuttle_path

    if not path.exists() or not path.is_dir():
        return False

    if path.stat().st_dev != snapshot.device_id:
        return False

    current_files = _snapshot_files(path)

    return (
        snapshot_fingerprint(current_files)
        == snapshot.fingerprint
    )
