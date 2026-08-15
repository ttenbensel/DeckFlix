from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    SnapshotDisposition,
    validate_snapshot_evidence,
)


def make_manager(
    tmp_path: Path,
    *,
    source_data: bytes = b"snapshot-data",
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    source = shuttle / "movie.mkv"
    source.write_bytes(source_data)

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-EVIDENCE-001",
    )

    return manager, source


def evidence_path(
    tmp_path: Path,
    data: bytes,
) -> Path:
    path = tmp_path / "evidence.mkv"
    path.write_bytes(data)
    return path


def test_valid_imported_evidence_is_safe(
    tmp_path: Path,
):
    manager, source = make_manager(
        tmp_path
    )

    evidence = evidence_path(
        tmp_path,
        b"snapshot-data",
    )

    from deckflix_app.operation.evidence import (
        file_sha256,
    )

    ledger = manager.require_ledger()

    ledger.mark_imported(
        Path("movie.mkv"),
        destination=evidence,
        sha256=file_sha256(evidence),
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.total == 1
    assert result.valid == 1
    assert result.invalid == 0
    assert result.unresolved == 0
    assert result.imported == 1
    assert result.safe is True
    assert result.coverage_percent == 100

    assert source.exists()


def test_missing_imported_evidence_becomes_unresolved(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path
    )

    missing = (
        tmp_path
        / "missing.mkv"
    )

    ledger = manager.require_ledger()

    ledger.mark_imported(
        Path("movie.mkv"),
        destination=missing,
        sha256="a" * 64,
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.safe is False
    assert result.invalid == 1
    assert result.unresolved == 1

    entry = ledger.get(
        Path("movie.mkv")
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_same_size_corrupt_imported_evidence_is_rejected(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        source_data=b"AAAAAAAA",
    )

    evidence = evidence_path(
        tmp_path,
        b"BBBBBBBB",
    )

    ledger = manager.require_ledger()

    ledger.mark_imported(
        Path("movie.mkv"),
        destination=evidence,
        sha256="0" * 64,
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.safe is False
    assert result.invalid == 1

    assert (
        ledger.get(Path("movie.mkv"))
        .disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_valid_identical_evidence_is_safe(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path
    )

    evidence = evidence_path(
        tmp_path,
        b"snapshot-data",
    )

    from deckflix_app.operation.evidence import (
        file_sha256,
    )

    manager.require_ledger().mark_identical(
        Path("movie.mkv"),
        existing_path=evidence,
        sha256=file_sha256(evidence),
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.safe is True
    assert result.identical == 1
    assert result.valid == 1


def test_valid_review_hold_evidence_is_safe(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path
    )

    evidence = evidence_path(
        tmp_path,
        b"snapshot-data",
    )

    from deckflix_app.operation.evidence import (
        file_sha256,
    )

    manager.require_ledger().mark_review_hold(
        Path("movie.mkv"),
        hold_path=evidence,
        sha256=file_sha256(evidence),
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.safe is True
    assert result.review_hold == 1
    assert result.valid == 1


def test_unresolved_entry_blocks_safe_status(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.total == 1
    assert result.valid == 0
    assert result.invalid == 0
    assert result.unresolved == 1
    assert result.safe is False
    assert result.coverage_percent == 0


def test_mixed_valid_evidence_requires_every_file(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    first = shuttle / "one.mkv"
    second = shuttle / "two.mkv"

    first.write_bytes(b"one")
    second.write_bytes(b"two")

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-EVIDENCE-002",
    )

    imported = tmp_path / "imported.mkv"
    imported.write_bytes(b"one")

    from deckflix_app.operation.evidence import (
        file_sha256,
    )

    manager.require_ledger().mark_imported(
        Path("one.mkv"),
        destination=imported,
        sha256=file_sha256(imported),
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.total == 2
    assert result.valid == 1
    assert result.unresolved == 1
    assert result.safe is False
    assert result.coverage_percent == 50
