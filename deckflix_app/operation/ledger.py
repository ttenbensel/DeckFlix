from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .models import ShuttleSnapshot


class SnapshotDisposition(str, Enum):
    IMPORTED = "IMPORTED"
    IDENTICAL = "IDENTICAL"
    REVIEW_HOLD = "REVIEW_HOLD"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class SnapshotDispositionEntry:
    relative_path: Path
    disposition: SnapshotDisposition
    evidence_path: Path | None = None
    sha256: str | None = None
    detail: str = ""


@dataclass(slots=True)
class SnapshotLedger:
    snapshot: ShuttleSnapshot
    entries: dict[Path, SnapshotDispositionEntry] = field(
        default_factory=dict
    )

    @property
    def total_files(self) -> int:
        return self.snapshot.file_count

    @property
    def accounted_files(self) -> int:
        return sum(
            1
            for entry in self.entries.values()
            if entry.disposition
            is not SnapshotDisposition.UNRESOLVED
        )

    @property
    def unresolved_files(self) -> int:
        return self.total_files - self.accounted_files

    @property
    def coverage_complete(self) -> bool:
        return (
            self.total_files > 0
            and self.accounted_files == self.total_files
            and self.unresolved_files == 0
        )

    @property
    def coverage_percent(self) -> int:
        if self.total_files <= 0:
            return 0

        return int(
            (
                self.accounted_files
                / self.total_files
            )
            * 100
        )

    def count(
        self,
        disposition: SnapshotDisposition,
    ) -> int:
        return sum(
            1
            for entry in self.entries.values()
            if entry.disposition is disposition
        )

    def get(
        self,
        relative_path: Path,
    ) -> SnapshotDispositionEntry | None:
        return self.entries.get(
            Path(relative_path)
        )

    def set(
        self,
        relative_path: Path,
        disposition: SnapshotDisposition,
        *,
        evidence_path: Path | None = None,
        sha256: str | None = None,
        detail: str = "",
    ) -> SnapshotDispositionEntry:
        relative_path = Path(
            relative_path
        )

        snapshot_paths = {
            item.relative_path
            for item in self.snapshot.files
        }

        if relative_path not in snapshot_paths:
            raise ValueError(
                "Ledger entry does not belong to "
                f"the shuttle snapshot: {relative_path}"
            )

        entry = SnapshotDispositionEntry(
            relative_path=relative_path,
            disposition=disposition,
            evidence_path=(
                Path(evidence_path)
                if evidence_path is not None
                else None
            ),
            sha256=sha256,
            detail=detail,
        )

        self.entries[
            relative_path
        ] = entry

        return entry

    def mark_imported(
        self,
        relative_path: Path,
        *,
        destination: Path,
        sha256: str,
    ) -> SnapshotDispositionEntry:
        return self.set(
            relative_path,
            SnapshotDisposition.IMPORTED,
            evidence_path=destination,
            sha256=sha256,
            detail="Imported and SHA-256 verified",
        )

    def mark_identical(
        self,
        relative_path: Path,
        *,
        existing_path: Path,
        sha256: str,
    ) -> SnapshotDispositionEntry:
        return self.set(
            relative_path,
            SnapshotDisposition.IDENTICAL,
            evidence_path=existing_path,
            sha256=sha256,
            detail=(
                "Existing library file is "
                "SHA-256 identical"
            ),
        )

    def mark_review_hold(
        self,
        relative_path: Path,
        *,
        hold_path: Path,
        sha256: str,
    ) -> SnapshotDispositionEntry:
        return self.set(
            relative_path,
            SnapshotDisposition.REVIEW_HOLD,
            evidence_path=hold_path,
            sha256=sha256,
            detail=(
                "Preserved in Review Hold and "
                "SHA-256 verified"
            ),
        )

    def mark_unresolved(
        self,
        relative_path: Path,
        *,
        detail: str = "",
    ) -> SnapshotDispositionEntry:
        return self.set(
            relative_path,
            SnapshotDisposition.UNRESOLVED,
            detail=detail,
        )

    @classmethod
    def from_snapshot(
        cls,
        snapshot: ShuttleSnapshot,
    ) -> "SnapshotLedger":
        ledger = cls(
            snapshot=snapshot
        )

        for item in snapshot.files:
            ledger.entries[
                item.relative_path
            ] = SnapshotDispositionEntry(
                relative_path=item.relative_path,
                disposition=(
                    SnapshotDisposition.UNRESOLVED
                ),
            )

        return ledger
