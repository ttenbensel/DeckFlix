from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Callable

from .ledger import SnapshotDisposition
from .manager import (
    InvalidOperationTransition,
    OperationManager,
)


@dataclass(frozen=True, slots=True)
class IdenticalReconciliationResult:
    candidates: int
    same_size: int
    identical: int
    different: int
    unavailable: int
    verified_bytes: int
    resumed: int = 0
    hashed: int = 0


@dataclass(frozen=True, slots=True)
class ReconciliationProgress:
    current: int
    total: int
    identical: int
    different: int
    unavailable: int
    verified_bytes: int
    path: Path
    resumed: int = 0
    hashed: int = 0


ProgressCallback = Callable[
    [ReconciliationProgress],
    None,
]


@dataclass(frozen=True, slots=True)
class _Candidate:
    relative_path: Path
    source: Path
    library: Path
    size: int
    modified_ns: int


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


def _snapshot_file_map(
    manager: OperationManager,
):
    operation = manager.require_operation()

    return {
        item.relative_path: item
        for item in operation.snapshot.files
    }


def _same_size_candidates(
    manager: OperationManager,
):
    operation = manager.require_operation()

    if manager.decisions is None:
        raise InvalidOperationTransition(
            "No decision queue is attached"
        )

    shuttle_path = (
        operation.snapshot
        .shuttle_path
        .resolve()
    )

    snapshot_files = (
        _snapshot_file_map(
            manager
        )
    )

    candidates: list[_Candidate] = []
    different = 0
    unavailable = 0

    for item in manager.decisions.items:
        incoming = item.incoming
        existing = item.existing

        if existing is None:
            continue

        if (
            incoming.path is None
            or existing.path is None
        ):
            unavailable += 1
            continue

        source = Path(
            incoming.path
        ).resolve()

        library = Path(
            existing.path
        ).resolve()

        try:
            relative_path = (
                source.relative_to(
                    shuttle_path
                )
            )

            snapshot_file = (
                snapshot_files[
                    relative_path
                ]
            )

            source_stat = source.stat()
            library_stat = library.stat()

        except (
            ValueError,
            KeyError,
            OSError,
        ):
            unavailable += 1
            continue

        if (
            source_stat.st_size
            != library_stat.st_size
        ):
            ledger = manager.require_ledger()
            entry = ledger.get(
                relative_path
            )

            if (
                entry is not None
                and entry.disposition
                is SnapshotDisposition.IDENTICAL
            ):
                ledger.mark_unresolved(
                    relative_path
                )

            different += 1
            continue

        candidates.append(
            _Candidate(
                relative_path=relative_path,
                source=source,
                library=library,
                size=source_stat.st_size,
                modified_ns=(
                    snapshot_file.modified_ns
                ),
            )
        )

    return (
        candidates,
        different,
        unavailable,
    )


def _can_resume_identical(
    manager: OperationManager,
    candidate: _Candidate,
) -> bool:
    """
    Return True only when persisted IDENTICAL evidence
    still belongs to this exact snapshot candidate and
    the current library file still matches the saved
    SHA-256 evidence.

    The shuttle itself has already been validated
    against the immutable operation snapshot.
    """
    ledger = manager.require_ledger()

    entry = ledger.get(
        candidate.relative_path
    )

    if entry is None:
        return False

    if (
        entry.disposition
        is not SnapshotDisposition.IDENTICAL
    ):
        return False

    if not entry.sha256:
        return False

    if len(entry.sha256) != 64:
        return False

    if entry.evidence_path is None:
        return False

    try:
        evidence = (
            Path(entry.evidence_path)
            .resolve()
        )

        library = (
            candidate.library.resolve()
        )

    except OSError:
        return False

    if evidence != library:
        return False

    try:
        source_stat = (
            candidate.source.stat()
        )

        library_stat = (
            candidate.library.stat()
        )

    except OSError:
        return False

    if (
        source_stat.st_size
        != candidate.size
    ):
        return False

    if (
        source_stat.st_mtime_ns
        != candidate.modified_ns
    ):
        return False

    if (
        library_stat.st_size
        != candidate.size
    ):
        return False

    try:
        current_library_hash = (
            file_sha256(
                candidate.library
            )
        )

    except OSError:
        return False

    if (
        current_library_hash
        != entry.sha256
    ):
        return False

    return True


def reconcile_identical_files(
    manager: OperationManager,
    *,
    progress: ProgressCallback | None = None,
) -> IdenticalReconciliationResult:
    """
    Account for shuttle files that already have a
    byte-for-byte identical library copy.

    Equal size is only a candidate filter.

    Existing IDENTICAL ledger evidence may be resumed
    when it still belongs to the same immutable shuttle
    snapshot and current library evidence path.

    Otherwise IDENTICAL is recorded only after SHA-256
    confirms both files are byte-for-byte identical.
    """
    manager.require_valid_snapshot()
    ledger = manager.require_ledger()

    if manager.decisions is None:
        raise InvalidOperationTransition(
            "No decision queue is attached"
        )

    candidates_total = sum(
        1
        for item in manager.decisions.items
        if item.existing is not None
    )

    (
        same_size_candidates,
        different,
        unavailable,
    ) = _same_size_candidates(
        manager
    )

    identical = 0
    verified_bytes = 0
    resumed = 0
    hashed = 0

    total = len(
        same_size_candidates
    )

    for current, candidate in enumerate(
        same_size_candidates,
        start=1,
    ):
        entry = ledger.get(
            candidate.relative_path
        )

        was_identical = (
            entry is not None
            and entry.disposition
            is SnapshotDisposition.IDENTICAL
        )

        if _can_resume_identical(
            manager,
            candidate,
        ):
            identical += 1
            resumed += 1
            verified_bytes += (
                candidate.size
            )

            if progress is not None:
                progress(
                    ReconciliationProgress(
                        current=current,
                        total=total,
                        identical=identical,
                        different=different,
                        unavailable=unavailable,
                        verified_bytes=verified_bytes,
                        path=candidate.source,
                        resumed=resumed,
                        hashed=hashed,
                    )
                )

            continue

        if was_identical:
            ledger.mark_unresolved(
                candidate.relative_path
            )

        hashed += 1

        try:
            source_hash = file_sha256(
                candidate.source
            )

            library_hash = file_sha256(
                candidate.library
            )

        except OSError:
            unavailable += 1

            if progress is not None:
                progress(
                    ReconciliationProgress(
                        current=current,
                        total=total,
                        identical=identical,
                        different=different,
                        unavailable=unavailable,
                        verified_bytes=verified_bytes,
                        path=candidate.source,
                        resumed=resumed,
                        hashed=hashed,
                    )
                )

            continue

        if source_hash != library_hash:
            different += 1

        else:
            ledger.mark_identical(
                candidate.relative_path,
                existing_path=(
                    candidate.library
                ),
                sha256=source_hash,
            )

            identical += 1
            verified_bytes += (
                candidate.size
            )

        if progress is not None:
            progress(
                ReconciliationProgress(
                    current=current,
                    total=total,
                    identical=identical,
                    different=different,
                    unavailable=unavailable,
                    verified_bytes=verified_bytes,
                    path=candidate.source,
                    resumed=resumed,
                    hashed=hashed,
                )
            )

    return IdenticalReconciliationResult(
        candidates=candidates_total,
        same_size=total,
        identical=identical,
        different=different,
        unavailable=unavailable,
        verified_bytes=verified_bytes,
        resumed=resumed,
        hashed=hashed,
    )
