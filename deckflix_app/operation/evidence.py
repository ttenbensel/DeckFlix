from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .ledger import SnapshotDisposition
from .manager import OperationManager


@dataclass(frozen=True, slots=True)
class EvidenceValidationResult:
    total: int
    valid: int
    invalid: int
    unresolved: int
    imported: int
    identical: int
    review_hold: int
    verified_bytes: int

    @property
    def safe(self) -> bool:
        return (
            self.total > 0
            and self.valid == self.total
            and self.invalid == 0
            and self.unresolved == 0
        )

    @property
    def coverage_percent(self) -> int:
        if self.total <= 0:
            return 0

        return int(
            self.valid
            / self.total
            * 100
        )


def file_sha256(
    path: Path,
) -> str:
    digest = sha256()

    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(
                8 * 1024 * 1024
            )

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def validate_snapshot_evidence(
    manager: OperationManager,
) -> EvidenceValidationResult:
    """
    Revalidate every accounted snapshot disposition.

    IMPORTED, IDENTICAL, and REVIEW_HOLD remain
    accounted only when their evidence file:

      - is recorded,
      - exists,
      - has the immutable snapshot size,
      - has a recorded SHA-256,
      - currently matches that SHA-256.

    Invalid evidence is conservatively demoted to
    UNRESOLVED.

    No evidence file is modified.
    """
    manager.require_valid_snapshot()

    operation = manager.require_operation()
    ledger = manager.require_ledger()

    snapshot_files = {
        item.relative_path: item
        for item in operation.snapshot.files
    }

    valid = 0
    invalid = 0
    verified_bytes = 0

    for relative_path in snapshot_files:
        entry = ledger.get(
            relative_path
        )

        if entry is None:
            ledger.mark_unresolved(
                relative_path,
                detail=(
                    "Missing snapshot ledger entry"
                ),
            )
            invalid += 1
            continue

        if (
            entry.disposition
            is SnapshotDisposition.UNRESOLVED
        ):
            continue

        snapshot_file = snapshot_files[
            relative_path
        ]

        evidence_valid = True
        reason = ""

        if entry.evidence_path is None:
            evidence_valid = False
            reason = "Evidence path is missing"

        elif not entry.sha256:
            evidence_valid = False
            reason = "Evidence SHA-256 is missing"

        elif len(entry.sha256) != 64:
            evidence_valid = False
            reason = "Evidence SHA-256 is invalid"

        if evidence_valid:
            evidence = Path(
                entry.evidence_path
            )

            try:
                evidence_stat = evidence.stat()

                if not evidence.is_file():
                    evidence_valid = False
                    reason = (
                        "Evidence path is not a file"
                    )

                elif (
                    evidence_stat.st_size
                    != snapshot_file.size
                ):
                    evidence_valid = False
                    reason = (
                        "Evidence size does not match "
                        "snapshot"
                    )

                elif (
                    file_sha256(evidence)
                    != entry.sha256
                ):
                    evidence_valid = False
                    reason = (
                        "Evidence SHA-256 does not match"
                    )

            except OSError as exc:
                evidence_valid = False
                reason = (
                    f"Evidence unavailable: {exc}"
                )

        if not evidence_valid:
            ledger.mark_unresolved(
                relative_path,
                detail=reason,
            )

            invalid += 1
            continue

        valid += 1
        verified_bytes += (
            snapshot_file.size
        )

    unresolved = ledger.count(
        SnapshotDisposition.UNRESOLVED
    )

    imported = ledger.count(
        SnapshotDisposition.IMPORTED
    )

    identical = ledger.count(
        SnapshotDisposition.IDENTICAL
    )

    review_hold = ledger.count(
        SnapshotDisposition.REVIEW_HOLD
    )

    return EvidenceValidationResult(
        total=ledger.total_files,
        valid=valid,
        invalid=invalid,
        unresolved=unresolved,
        imported=imported,
        identical=identical,
        review_hold=review_hold,
        verified_bytes=verified_bytes,
    )
