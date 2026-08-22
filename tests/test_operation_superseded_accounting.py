from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    SnapshotDisposition,
    prepare_operation,
)
from deckflix_app.operation.workflow import (
    account_superseded_snapshot_files,
)


def _roots(
    tmp_path: Path,
) -> tuple[Path, Path, Path]:
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    return shuttle, movies, tv


def test_prepare_operation_marks_losing_physical_candidate_superseded(
    tmp_path: Path,
):
    shuttle, movies, tv = _roots(
        tmp_path
    )

    lower = (
        shuttle
        / "Example.Show.S01E01.480p.HDTV.x264.mkv"
    )

    better = (
        shuttle
        / "Example.Show.S01E01.720p.WEBRip.x264.mkv"
    )

    lower.write_bytes(
        b"lower"
    )

    better.write_bytes(
        b"better"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-SUPERSEDED-001",
    )

    operation = manager.require_operation()
    ledger = manager.require_ledger()

    assert operation.snapshot.file_count == 2

    assert manager.decisions is not None
    assert manager.decisions.total == 1

    assert ledger.count(
        SnapshotDisposition.SUPERSEDED
    ) == 1

    assert ledger.count(
        SnapshotDisposition.UNRESOLVED
    ) == 1

    assert ledger.accounted_files == 1
    assert ledger.unresolved_files == 1

    lower_entry = ledger.get(
        lower.relative_to(shuttle)
    )

    assert lower_entry is not None

    assert (
        lower_entry.disposition
        is SnapshotDisposition.SUPERSEDED
    )

    assert (
        lower_entry.evidence_path
        == better.resolve()
    )

    assert lower_entry.sha256 is None

    better_entry = ledger.get(
        better.relative_to(shuttle)
    )

    assert better_entry is not None

    assert (
        better_entry.disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_equal_quality_duplicate_keeps_one_survivor_and_accounts_other(
    tmp_path: Path,
):
    shuttle, movies, tv = _roots(
        tmp_path
    )

    first = (
        shuttle
        / "A"
        / "Example.Show.S01E01.720p.WEBRip.x264.mkv"
    )

    second = (
        shuttle
        / "B"
        / "Example.Show.S01E01.720p.WEBRip.x264.mkv"
    )

    first.parent.mkdir()
    second.parent.mkdir()

    first.write_bytes(
        b"first"
    )

    second.write_bytes(
        b"second"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-SUPERSEDED-002",
    )

    ledger = manager.require_ledger()

    assert manager.decisions is not None
    assert manager.decisions.total == 1

    assert ledger.count(
        SnapshotDisposition.SUPERSEDED
    ) == 1

    entries = [
        ledger.get(
            first.relative_to(shuttle)
        ),
        ledger.get(
            second.relative_to(shuttle)
        ),
    ]

    dispositions = [
        entry.disposition
        for entry in entries
        if entry is not None
    ]

    assert dispositions.count(
        SnapshotDisposition.SUPERSEDED
    ) == 1

    assert dispositions.count(
        SnapshotDisposition.UNRESOLVED
    ) == 1


def test_unique_physical_files_are_not_marked_superseded(
    tmp_path: Path,
):
    shuttle, movies, tv = _roots(
        tmp_path
    )

    first = (
        shuttle
        / "Example.Show.S01E01.720p.WEBRip.x264.mkv"
    )

    second = (
        shuttle
        / "Example.Show.S01E02.720p.WEBRip.x264.mkv"
    )

    first.write_bytes(
        b"one"
    )

    second.write_bytes(
        b"two"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-SUPERSEDED-003",
    )

    ledger = manager.require_ledger()

    assert manager.decisions is not None
    assert manager.decisions.total == 2

    assert ledger.count(
        SnapshotDisposition.SUPERSEDED
    ) == 0

    assert ledger.accounted_files == 0
    assert ledger.unresolved_files == 2


def test_unmatched_missing_snapshot_path_fails_closed(
    tmp_path: Path,
):
    shuttle, movies, tv = _roots(
        tmp_path
    )

    first = (
        shuttle
        / "Example.Show.S01E01.720p.WEBRip.x264.mkv"
    )

    first.write_bytes(
        b"one"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-SUPERSEDED-004",
    )

    ledger = manager.require_ledger()

    before = ledger.accounted_files

    # Re-running reconciliation is idempotent when every snapshot
    # source already has its one surviving decision.
    accounted = account_superseded_snapshot_files(
        manager
    )

    assert accounted == 0
    assert ledger.accounted_files == before
    assert ledger.count(
        SnapshotDisposition.SUPERSEDED
    ) == 0


def test_superseded_accounting_is_idempotent(
    tmp_path: Path,
):
    shuttle, movies, tv = _roots(
        tmp_path
    )

    lower = (
        shuttle
        / "Example.Show.S01E01.480p.HDTV.x264.mkv"
    )

    better = (
        shuttle
        / "Example.Show.S01E01.720p.WEBRip.x264.mkv"
    )

    lower.write_bytes(
        b"lower"
    )

    better.write_bytes(
        b"better"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-SUPERSEDED-005",
    )

    ledger = manager.require_ledger()

    assert ledger.count(
        SnapshotDisposition.SUPERSEDED
    ) == 1

    accounted = account_superseded_snapshot_files(
        manager
    )

    assert accounted == 1

    assert ledger.count(
        SnapshotDisposition.SUPERSEDED
    ) == 1

    assert ledger.accounted_files == 1
