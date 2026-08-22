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
    superseded: int
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


def _validate_superseded_evidence(
    *,
    entry,
    snapshot_paths: set[Path],
    shuttle_path: Path,
) -> tuple[bool, str]:
    """
    Validate SUPERSEDED evidence without claiming byte identity.

    A superseded snapshot file is accounted only when its recorded
    survivor:

      - exists,
      - is a regular file,
      - remains inside the same shuttle,
      - is itself a member of the immutable shuttle snapshot.

    No size or SHA-256 equality is required. SUPERSEDED describes
    logical-media deduplication, not byte-for-byte identity.
    """
    if entry.evidence_path is None:
        return (
            False,
            "Superseded survivor path is missing",
        )

    if entry.sha256 is not None:
        return (
            False,
            "Superseded evidence must not claim SHA-256 identity",
        )

    try:
        evidence = Path(
            entry.evidence_path
        ).resolve()

        shuttle = shuttle_path.resolve()

    except OSError as exc:
        return (
            False,
            f"Superseded survivor unavailable: {exc}",
        )

    try:
        relative_survivor = (
            evidence.relative_to(
                shuttle
            )
        )

    except ValueError:
        return (
            False,
            "Superseded survivor is outside shuttle",
        )

    if relative_survivor not in snapshot_paths:
        return (
            False,
            "Superseded survivor is not in shuttle snapshot",
        )

    try:
        if not evidence.is_file():
            return (
                False,
                "Superseded survivor is not a file",
            )

    except OSError as exc:
        return (
            False,
            f"Superseded survivor unavailable: {exc}",
        )

    return True, ""


def validate_snapshot_evidence(
    manager: OperationManager,
) -> EvidenceValidationResult:
    """
    Revalidate every accounted snapshot disposition.

    IMPORTED, IDENTICAL, and REVIEW_HOLD remain accounted only
    when their evidence file:

      - is recorded,
      - exists,
      - has the immutable snapshot size,
      - has a recorded SHA-256,
      - currently matches that SHA-256.

    SUPERSEDED remains accounted only when its surviving physical
    shuttle source:

      - is recorded,
      - exists as a regular file,
      - remains inside the same shuttle,
      - belongs to the immutable shuttle snapshot,
      - carries no SHA-256 identity claim.

    Invalid evidence is conservatively demoted to UNRESOLVED.

    No evidence file is modified.
    """
    manager.require_valid_snapshot()

    operation = manager.require_operation()
    ledger = manager.require_ledger()

    snapshot_files = {
        item.relative_path: item
        for item in operation.snapshot.files
    }

    snapshot_paths = set(
        snapshot_files
    )

    shuttle_path = (
        operation.snapshot
        .shuttle_path
    )

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

        if (
            entry.disposition
            is SnapshotDisposition.SUPERSEDED
        ):
            (
                evidence_valid,
                reason,
            ) = _validate_superseded_evidence(
                entry=entry,
                snapshot_paths=snapshot_paths,
                shuttle_path=shuttle_path,
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
            continue

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

    superseded = ledger.count(
        SnapshotDisposition.SUPERSEDED
    )

    return EvidenceValidationResult(
        total=ledger.total_files,
        valid=valid,
        invalid=invalid,
        unresolved=unresolved,
        imported=imported,
        identical=identical,
        review_hold=review_hold,
        superseded=superseded,
        verified_bytes=verified_bytes,
    )
