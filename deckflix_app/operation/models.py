from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class OperationState(str, Enum):
    CREATED = "CREATED"
    SNAPSHOT_READY = "SNAPSHOT_READY"
    INVALIDATED = "INVALIDATED"
    APPROVED = "APPROVED"
    IMPORTING = "IMPORTING"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True, slots=True)
class SnapshotFile:
    relative_path: Path
    size: int
    modified_ns: int


@dataclass(frozen=True, slots=True)
class ShuttleSnapshot:
    shuttle_path: Path
    device_id: int
    files: tuple[SnapshotFile, ...]
    total_bytes: int
    fingerprint: str
    created_at: datetime

    @property
    def file_count(self) -> int:
        return len(self.files)


@dataclass(frozen=True, slots=True)
class Operation:
    id: str
    state: OperationState
    snapshot: ShuttleSnapshot
    created_at: datetime
