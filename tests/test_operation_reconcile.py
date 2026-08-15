from pathlib import Path

from deckflix_app.decision import (
    DecisionQueue,
    DecisionQueueItem,
)
from deckflix_app.decision.actions import Action
from deckflix_app.decision.models import Decision
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.operation import (
    OperationManager,
    SnapshotDisposition,
    reconcile_identical_files,
)


def media(
    path: Path,
    *,
    size: int,
) -> MediaMetadata:
    return MediaMetadata(
        media_type="movie",
        title="Test Movie",
        year=2026,
        season=None,
        episode=None,
        resolution="1080p",
        source="bluray",
        video_codec="hevc",
        container="mkv",
        path=path,
        size=size,
    )


def decision() -> Decision:
    return Decision(
        action=Action.UPGRADE,
        reason="test",
        existing_score=1,
        incoming_score=2,
    )


def manager_with_pair(
    tmp_path: Path,
    *,
    source_data: bytes,
    library_data: bytes,
):
    shuttle = tmp_path / "shuttle"
    library = tmp_path / "library"

    shuttle.mkdir()
    library.mkdir()

    source = shuttle / "movie.mkv"
    existing = library / "movie.mkv"

    source.write_bytes(source_data)
    existing.write_bytes(library_data)

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-RECONCILE-001",
    )

    manager.attach_decisions(
        DecisionQueue(
            items=[
                DecisionQueueItem(
                    incoming=media(
                        source,
                        size=len(source_data),
                    ),
                    existing=media(
                        existing,
                        size=len(library_data),
                    ),
                    decision=decision(),
                )
            ]
        )
    )

    return (
        manager,
        source,
        existing,
    )


def relative_path(
    manager: OperationManager,
    source: Path,
) -> Path:
    return source.relative_to(
        manager.require_operation()
        .snapshot
        .shuttle_path
    )


def test_identical_file_is_accounted(
    tmp_path: Path,
):
    manager, source, existing = (
        manager_with_pair(
            tmp_path,
            source_data=b"same-data",
            library_data=b"same-data",
        )
    )

    result = reconcile_identical_files(
        manager
    )

    assert result.candidates == 1
    assert result.same_size == 1
    assert result.identical == 1
    assert result.different == 0
    assert result.unavailable == 0
    assert result.verified_bytes == 9
    assert result.resumed == 0
    assert result.hashed == 1

    entry = (
        manager.require_ledger()
        .get(
            relative_path(
                manager,
                source,
            )
        )
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.IDENTICAL
    )

    assert (
        entry.evidence_path
        == existing.resolve()
    )

    assert entry.sha256 is not None
    assert len(entry.sha256) == 64

    assert (
        manager.require_ledger()
        .unresolved_files
        == 0
    )


def test_second_run_resumes_identical_evidence(
    tmp_path: Path,
):
    manager, _, _ = (
        manager_with_pair(
            tmp_path,
            source_data=b"same-data",
            library_data=b"same-data",
        )
    )

    first = reconcile_identical_files(
        manager
    )

    assert first.hashed == 1
    assert first.resumed == 0

    second = reconcile_identical_files(
        manager
    )

    assert second.identical == 1
    assert second.resumed == 1
    assert second.hashed == 0


def test_same_size_different_content_stays_unresolved(
    tmp_path: Path,
):
    manager, source, _ = (
        manager_with_pair(
            tmp_path,
            source_data=b"AAAA",
            library_data=b"BBBB",
        )
    )

    result = reconcile_identical_files(
        manager
    )

    assert result.candidates == 1
    assert result.same_size == 1
    assert result.identical == 0
    assert result.different == 1
    assert result.resumed == 0
    assert result.hashed == 1

    entry = (
        manager.require_ledger()
        .get(
            relative_path(
                manager,
                source,
            )
        )
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_different_size_is_not_hashed_or_accounted(
    tmp_path: Path,
):
    manager, source, _ = (
        manager_with_pair(
            tmp_path,
            source_data=b"AAAA",
            library_data=b"BBBBB",
        )
    )

    result = reconcile_identical_files(
        manager
    )

    assert result.candidates == 1
    assert result.same_size == 0
    assert result.identical == 0
    assert result.different == 1
    assert result.hashed == 0

    entry = (
        manager.require_ledger()
        .get(
            relative_path(
                manager,
                source,
            )
        )
    )

    assert (
        entry.disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_missing_existing_file_stays_unresolved(
    tmp_path: Path,
):
    manager, source, existing = (
        manager_with_pair(
            tmp_path,
            source_data=b"same",
            library_data=b"same",
        )
    )

    existing.unlink()

    result = reconcile_identical_files(
        manager
    )

    assert result.candidates == 1
    assert result.identical == 0
    assert result.unavailable == 1
    assert result.hashed == 0

    assert (
        manager.require_ledger()
        .get(
            relative_path(
                manager,
                source,
            )
        )
        .disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_missing_identical_evidence_path_forces_rehash(
    tmp_path: Path,
):
    manager, source, existing = (
        manager_with_pair(
            tmp_path,
            source_data=b"same-data",
            library_data=b"same-data",
        )
    )

    first = reconcile_identical_files(
        manager
    )

    assert first.identical == 1

    entry = (
        manager.require_ledger()
        .get(
            relative_path(
                manager,
                source,
            )
        )
    )

    assert entry is not None
    assert entry.sha256 is not None

    manager.require_ledger().set(
        relative_path(
            manager,
            source,
        ),
        SnapshotDisposition.IDENTICAL,
        evidence_path=None,
        sha256=entry.sha256,
    )

    second = reconcile_identical_files(
        manager
    )

    assert second.identical == 1
    assert second.resumed == 0
    assert second.hashed == 1

    repaired = (
        manager.require_ledger()
        .get(
            relative_path(
                manager,
                source,
            )
        )
    )

    assert repaired is not None
    assert (
        repaired.evidence_path
        == existing.resolve()
    )


def test_invalid_identical_hash_forces_rehash(
    tmp_path: Path,
):
    manager, source, existing = (
        manager_with_pair(
            tmp_path,
            source_data=b"same-data",
            library_data=b"same-data",
        )
    )

    reconcile_identical_files(
        manager
    )

    manager.require_ledger().set(
        relative_path(
            manager,
            source,
        ),
        SnapshotDisposition.IDENTICAL,
        evidence_path=existing,
        sha256="invalid",
    )

    result = reconcile_identical_files(
        manager
    )

    assert result.identical == 1
    assert result.resumed == 0
    assert result.hashed == 1

    repaired = (
        manager.require_ledger()
        .get(
            relative_path(
                manager,
                source,
            )
        )
    )

    assert repaired is not None
    assert repaired.sha256 is not None
    assert len(repaired.sha256) == 64


def test_changed_library_size_forces_normal_reconciliation(
    tmp_path: Path,
):
    manager, source, existing = (
        manager_with_pair(
            tmp_path,
            source_data=b"same-data",
            library_data=b"same-data",
        )
    )

    first = reconcile_identical_files(
        manager
    )

    assert first.identical == 1

    existing.write_bytes(
        b"changed-library-data"
    )

    result = reconcile_identical_files(
        manager
    )

    assert result.identical == 0
    assert result.resumed == 0
    assert result.hashed == 0
    assert result.different == 1

    # Stale IDENTICAL evidence must immediately lose
    # its accounted status.
    entry = (
        manager.require_ledger()
        .get(
            relative_path(
                manager,
                source,
            )
        )
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.UNRESOLVED
    )

    assert (
        manager.require_ledger()
        .unresolved_files
        == 1
    )


def test_stale_same_size_evidence_is_demoted_then_repaired(
    tmp_path: Path,
):
    manager, source, existing = (
        manager_with_pair(
            tmp_path,
            source_data=b"same-data",
            library_data=b"same-data",
        )
    )

    first = reconcile_identical_files(
        manager
    )

    assert first.identical == 1

    relative = relative_path(
        manager,
        source,
    )

    manager.require_ledger().set(
        relative,
        SnapshotDisposition.IDENTICAL,
        evidence_path=existing,
        sha256="0" * 64,
    )

    second = reconcile_identical_files(
        manager
    )

    assert second.identical == 1
    assert second.resumed == 0
    assert second.hashed == 1

    entry = (
        manager.require_ledger()
        .get(relative)
    )

    assert entry is not None
    assert (
        entry.disposition
        is SnapshotDisposition.IDENTICAL
    )

    assert entry.sha256 != "0" * 64
    assert len(entry.sha256) == 64
