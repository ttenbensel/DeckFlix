from datetime import datetime
from pathlib import Path
from typing import cast

from deckflix_app.decision import Decision
from deckflix_app.importer import (
    ImportJob,
    ImportQueue,
    ImportResult,
    ShuttleSafetyChecker,
)
from deckflix_app.operation import (
    ShuttleSnapshot,
    SnapshotFile,
    SnapshotLedger,
)


def build_fixture(
    tmp_path: Path,
):
    shuttle = (
        tmp_path
        / "shuttle"
    )

    library = (
        tmp_path
        / "library"
    )

    temp = (
        tmp_path
        / "temp"
    )

    shuttle.mkdir()
    library.mkdir()
    temp.mkdir()

    imported = (
        shuttle
        / "Imported.mkv"
    )

    unresolved = (
        shuttle
        / "Unresolved.mkv"
    )

    imported.write_bytes(
        b"imported"
    )

    unresolved.write_bytes(
        b"unresolved"
    )

    destination = (
        library
        / "Imported.mkv"
    )

    destination.write_bytes(
        b"imported"
    )

    snapshot = ShuttleSnapshot(
        shuttle_path=shuttle,
        device_id=(
            shuttle.stat().st_dev
        ),
        files=(
            SnapshotFile(
                relative_path=Path(
                    "Imported.mkv"
                ),
                size=imported.stat().st_size,
                modified_ns=(
                    imported.stat().st_mtime_ns
                ),
            ),
            SnapshotFile(
                relative_path=Path(
                    "Unresolved.mkv"
                ),
                size=unresolved.stat().st_size,
                modified_ns=(
                    unresolved.stat().st_mtime_ns
                ),
            ),
        ),
        total_bytes=(
            imported.stat().st_size
            + unresolved.stat().st_size
        ),
        fingerprint="test",
        created_at=datetime(
            2026,
            8,
            12,
            12,
            0,
            0,
        ),
    )

    ledger = (
        SnapshotLedger.from_snapshot(
            snapshot
        )
    )

    job = ImportJob(
        source=imported,
        destination=destination,
        decision=cast(
            Decision,
            object(),
        ),
        copied=True,
        verified=True,
        completed=True,
    )

    queue = ImportQueue()
    queue.add(job)

    result = ImportResult(
        total=1,
        completed=1,
        failed=0,
    )

    return (
        shuttle,
        temp,
        queue,
        result,
        ledger,
        destination,
    )


def test_unresolved_snapshot_blocks_safe_to_empty(
    tmp_path: Path,
):
    (
        shuttle,
        temp,
        queue,
        result,
        ledger,
        destination,
    ) = build_fixture(
        tmp_path
    )

    ledger.mark_imported(
        Path("Imported.mkv"),
        destination=destination,
        sha256="a" * 64,
    )

    checker = (
        ShuttleSafetyChecker()
    )

    safety = checker.check(
        queue=queue,
        import_result=result,
        shuttle_path=shuttle,
        temp_dir=temp,
    )

    assert safety.safe is True

    checker.apply_snapshot_coverage(
        safety,
        ledger=ledger,
        required=True,
    )

    assert safety.safe is False
    assert safety.status == "NOT SAFE TO EMPTY"

    assert (
        safety.snapshot_files
        == 2
    )

    assert (
        safety.snapshot_accounted
        == 1
    )

    assert (
        safety.snapshot_unresolved
        == 1
    )

    assert (
        safety.snapshot_coverage_percent
        == 50
    )

    assert (
        safety.snapshot_coverage_complete
        is False
    )


def test_full_snapshot_coverage_allows_safe_to_empty(
    tmp_path: Path,
):
    (
        shuttle,
        temp,
        queue,
        result,
        ledger,
        destination,
    ) = build_fixture(
        tmp_path
    )

    ledger.mark_imported(
        Path("Imported.mkv"),
        destination=destination,
        sha256="a" * 64,
    )

    ledger.mark_review_hold(
        Path("Unresolved.mkv"),
        hold_path=(
            tmp_path
            / "review-hold"
            / "Unresolved.mkv"
        ),
        sha256="b" * 64,
    )

    checker = (
        ShuttleSafetyChecker()
    )

    safety = checker.check(
        queue=queue,
        import_result=result,
        shuttle_path=shuttle,
        temp_dir=temp,
    )

    checker.apply_snapshot_coverage(
        safety,
        ledger=ledger,
        required=True,
    )

    assert safety.safe is True
    assert safety.status == "SAFE TO EMPTY"

    assert (
        safety.snapshot_files
        == 2
    )

    assert (
        safety.snapshot_accounted
        == 2
    )

    assert (
        safety.snapshot_unresolved
        == 0
    )

    assert (
        safety.snapshot_imported
        == 1
    )

    assert (
        safety.snapshot_review_hold
        == 1
    )

    assert (
        safety.snapshot_coverage_percent
        == 100
    )

    assert (
        safety.snapshot_coverage_complete
        is True
    )


def test_missing_ledger_blocks_required_coverage(
    tmp_path: Path,
):
    (
        shuttle,
        temp,
        queue,
        result,
        _,
        _,
    ) = build_fixture(
        tmp_path
    )

    checker = (
        ShuttleSafetyChecker()
    )

    safety = checker.check(
        queue=queue,
        import_result=result,
        shuttle_path=shuttle,
        temp_dir=temp,
    )

    checker.apply_snapshot_coverage(
        safety,
        ledger=None,
        required=True,
    )

    assert safety.safe is False

    assert any(
        "ledger is unavailable"
        in reason.lower()
        for reason in safety.reasons
    )


def test_legacy_safety_does_not_require_ledger(
    tmp_path: Path,
):
    (
        shuttle,
        temp,
        queue,
        result,
        _,
        _,
    ) = build_fixture(
        tmp_path
    )

    safety = (
        ShuttleSafetyChecker()
        .check(
            queue=queue,
            import_result=result,
            shuttle_path=shuttle,
            temp_dir=temp,
        )
    )

    assert safety.safe is True

    assert (
        safety.snapshot_coverage_required
        is False
    )
