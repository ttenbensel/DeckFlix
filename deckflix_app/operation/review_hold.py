from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import shutil

from .ledger import SnapshotDisposition
from .manager import OperationManager


@dataclass(frozen=True, slots=True)
class ReviewHoldProgress:
    current: int
    total: int
    completed: int
    resumed: int
    failed: int
    verified_bytes: int
    source: Path
    destination: Path
    message: str


@dataclass(frozen=True, slots=True)
class ReviewHoldFailure:
    source: Path
    destination: Path
    error: str


@dataclass(frozen=True, slots=True)
class ReviewHoldResult:
    total: int
    completed: int
    resumed: int
    failed: int
    verified_bytes: int
    failures: tuple[ReviewHoldFailure, ...]


ProgressCallback = Callable[
    [ReviewHoldProgress],
    None,
]


def file_sha256(path: Path) -> str:
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


def _emit(
    callback: ProgressCallback | None,
    event: ReviewHoldProgress,
) -> None:
    if callback is not None:
        callback(event)


def preserve_unresolved_in_review_hold(
    manager: OperationManager,
    *,
    review_hold_directory: Path,
    progress: ProgressCallback | None = None,
) -> ReviewHoldResult:
    """
    Preserve every currently UNRESOLVED shuttle file in
    an operation-specific Review Hold.

    A ledger entry becomes REVIEW_HOLD only after the
    destination is SHA-256 verified against the shuttle
    source.

    Existing valid Review Hold copies are resumed.

    The shuttle source is never moved or deleted.
    """
    manager.require_valid_snapshot()

    operation = manager.require_operation()
    ledger = manager.require_ledger()

    shuttle_root = (
        operation.snapshot
        .shuttle_path
        .resolve()
    )

    hold_root = (
        Path(review_hold_directory)
        .resolve()
        / operation.id
    )

    unresolved = [
        entry
        for entry in ledger.entries.values()
        if (
            entry.disposition
            is SnapshotDisposition.UNRESOLVED
        )
    ]

    total = len(unresolved)
    completed = 0
    resumed = 0
    failed = 0
    verified_bytes = 0
    failures: list[ReviewHoldFailure] = []

    for current, entry in enumerate(
        unresolved,
        start=1,
    ):
        relative = entry.relative_path
        source = shuttle_root / relative
        destination = hold_root / relative

        try:
            source = source.resolve()

            source.relative_to(
                shuttle_root
            )

            source_stat = source.stat()

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if destination.exists():
                destination_stat = (
                    destination.stat()
                )

                if (
                    destination_stat.st_size
                    == source_stat.st_size
                ):
                    source_hash = file_sha256(
                        source
                    )

                    destination_hash = file_sha256(
                        destination
                    )

                    if (
                        source_hash
                        == destination_hash
                    ):
                        ledger.mark_review_hold(
                            relative,
                            hold_path=destination,
                            sha256=source_hash,
                        )

                        completed += 1
                        resumed += 1
                        verified_bytes += (
                            source_stat.st_size
                        )

                        _emit(
                            progress,
                            ReviewHoldProgress(
                                current=current,
                                total=total,
                                completed=completed,
                                resumed=resumed,
                                failed=failed,
                                verified_bytes=(
                                    verified_bytes
                                ),
                                source=source,
                                destination=(
                                    destination
                                ),
                                message=(
                                    "Verified existing "
                                    "Review Hold copy"
                                ),
                            ),
                        )

                        continue

                destination.unlink()

            temporary = destination.with_name(
                destination.name
                + ".deckflix-part"
            )

            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

            shutil.copy2(
                source,
                temporary,
            )

            source_hash = file_sha256(
                source
            )

            temporary_hash = file_sha256(
                temporary
            )

            if source_hash != temporary_hash:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

                raise RuntimeError(
                    "Review Hold SHA-256 "
                    "verification failed"
                )

            temporary.replace(
                destination
            )

            ledger.mark_review_hold(
                relative,
                hold_path=destination,
                sha256=source_hash,
            )

            completed += 1
            verified_bytes += (
                source_stat.st_size
            )

            _emit(
                progress,
                ReviewHoldProgress(
                    current=current,
                    total=total,
                    completed=completed,
                    resumed=resumed,
                    failed=failed,
                    verified_bytes=(
                        verified_bytes
                    ),
                    source=source,
                    destination=destination,
                    message="Copied and verified",
                ),
            )

        except (
            OSError,
            RuntimeError,
            ValueError,
        ) as exc:
            failed += 1

            failures.append(
                ReviewHoldFailure(
                    source=source,
                    destination=destination,
                    error=str(exc),
                )
            )

            _emit(
                progress,
                ReviewHoldProgress(
                    current=current,
                    total=total,
                    completed=completed,
                    resumed=resumed,
                    failed=failed,
                    verified_bytes=(
                        verified_bytes
                    ),
                    source=source,
                    destination=destination,
                    message=f"FAILED: {exc}",
                ),
            )

    return ReviewHoldResult(
        total=total,
        completed=completed,
        resumed=resumed,
        failed=failed,
        verified_bytes=verified_bytes,
        failures=tuple(failures),
    )


@dataclass(frozen=True, slots=True)
class ReviewHoldValidationResult:
    checked: int
    valid: int
    invalid: int
    verified_bytes: int


def validate_review_hold_evidence(
    manager: OperationManager,
) -> ReviewHoldValidationResult:
    """
    Revalidate every REVIEW_HOLD ledger entry.

    REVIEW_HOLD remains accounted only when:
      - an evidence path is recorded,
      - a SHA-256 is recorded,
      - the evidence file exists,
      - its size matches the immutable shuttle snapshot,
      - its current SHA-256 matches the recorded SHA-256.

    Failed evidence is immediately demoted to UNRESOLVED.
    """
    manager.require_valid_snapshot()

    operation = manager.require_operation()
    ledger = manager.require_ledger()

    snapshot_files = {
        item.relative_path: item
        for item in operation.snapshot.files
    }

    entries = [
        entry
        for entry in ledger.entries.values()
        if (
            entry.disposition
            is SnapshotDisposition.REVIEW_HOLD
        )
    ]

    checked = 0
    valid = 0
    invalid = 0
    verified_bytes = 0

    for entry in entries:
        checked += 1

        snapshot_file = snapshot_files.get(
            entry.relative_path
        )

        evidence_valid = True

        if snapshot_file is None:
            evidence_valid = False

        if entry.evidence_path is None:
            evidence_valid = False

        if not entry.sha256:
            evidence_valid = False

        if (
            entry.sha256 is not None
            and len(entry.sha256) != 64
        ):
            evidence_valid = False

        if evidence_valid:
            evidence = Path(
                entry.evidence_path
            )

            try:
                evidence_stat = (
                    evidence.stat()
                )

                if (
                    evidence_stat.st_size
                    != snapshot_file.size
                ):
                    evidence_valid = False

                elif (
                    file_sha256(evidence)
                    != entry.sha256
                ):
                    evidence_valid = False

            except OSError:
                evidence_valid = False

        if not evidence_valid:
            ledger.mark_unresolved(
                entry.relative_path
            )

            invalid += 1
            continue

        valid += 1
        verified_bytes += (
            snapshot_file.size
        )

    return ReviewHoldValidationResult(
        checked=checked,
        valid=valid,
        invalid=invalid,
        verified_bytes=verified_bytes,
    )
