from datetime import datetime
from pathlib import Path

import pytest

from deckflix_app.operation.ledger import (
    SnapshotDisposition,
    SnapshotLedger,
)
from deckflix_app.operation.models import (
    ShuttleSnapshot,
    SnapshotFile,
)


def make_snapshot(
    tmp_path: Path,
) -> ShuttleSnapshot:
    shuttle = tmp_path / "shuttle"

    return ShuttleSnapshot(
        shuttle_path=shuttle,
        device_id=123,
        files=(
            SnapshotFile(
                relative_path=Path(
                    "Movies/Alien.mkv"
                ),
                size=100,
                modified_ns=1,
            ),
            SnapshotFile(
                relative_path=Path(
                    "TV/1883.S01E01.mkv"
                ),
                size=200,
                modified_ns=2,
            ),
            SnapshotFile(
                relative_path=Path(
                    "Extras/Bonus.mkv"
                ),
                size=300,
                modified_ns=3,
            ),
        ),
        total_bytes=600,
        fingerprint="abc123",
        created_at=datetime(
            2026,
            8,
            12,
            12,
            0,
            0,
        ),
    )


def test_ledger_starts_unresolved(
    tmp_path: Path,
):
    ledger = SnapshotLedger.from_snapshot(
        make_snapshot(tmp_path)
    )

    assert ledger.total_files == 3
    assert ledger.accounted_files == 0
    assert ledger.unresolved_files == 3
    assert ledger.coverage_percent == 0
    assert ledger.coverage_complete is False

    assert (
        ledger.count(
            SnapshotDisposition.UNRESOLVED
        )
        == 3
    )


def test_mark_imported_accounts_for_file(
    tmp_path: Path,
):
    ledger = SnapshotLedger.from_snapshot(
        make_snapshot(tmp_path)
    )

    entry = ledger.mark_imported(
        Path("Movies/Alien.mkv"),
        destination=(
            tmp_path
            / "library"
            / "Alien.mkv"
        ),
        sha256="hash-imported",
    )

    assert (
        entry.disposition
        is SnapshotDisposition.IMPORTED
    )

    assert ledger.accounted_files == 1
    assert ledger.unresolved_files == 2
    assert ledger.coverage_complete is False


def test_mark_identical_accounts_for_file(
    tmp_path: Path,
):
    ledger = SnapshotLedger.from_snapshot(
        make_snapshot(tmp_path)
    )

    entry = ledger.mark_identical(
        Path("TV/1883.S01E01.mkv"),
        existing_path=(
            tmp_path
            / "library"
            / "1883.S01E01.mkv"
        ),
        sha256="hash-identical",
    )

    assert (
        entry.disposition
        is SnapshotDisposition.IDENTICAL
    )

    assert (
        ledger.count(
            SnapshotDisposition.IDENTICAL
        )
        == 1
    )


def test_mark_review_hold_accounts_for_file(
    tmp_path: Path,
):
    ledger = SnapshotLedger.from_snapshot(
        make_snapshot(tmp_path)
    )

    entry = ledger.mark_review_hold(
        Path("Extras/Bonus.mkv"),
        hold_path=(
            tmp_path
            / "review-hold"
            / "Bonus.mkv"
        ),
        sha256="hash-hold",
    )

    assert (
        entry.disposition
        is SnapshotDisposition.REVIEW_HOLD
    )

    assert (
        ledger.count(
            SnapshotDisposition.REVIEW_HOLD
        )
        == 1
    )


def test_full_coverage_requires_every_file(
    tmp_path: Path,
):
    ledger = SnapshotLedger.from_snapshot(
        make_snapshot(tmp_path)
    )

    ledger.mark_imported(
        Path("Movies/Alien.mkv"),
        destination=(
            tmp_path
            / "library"
            / "Alien.mkv"
        ),
        sha256="one",
    )

    ledger.mark_identical(
        Path("TV/1883.S01E01.mkv"),
        existing_path=(
            tmp_path
            / "library"
            / "1883.S01E01.mkv"
        ),
        sha256="two",
    )

    assert ledger.coverage_complete is False
    assert ledger.accounted_files == 2
    assert ledger.unresolved_files == 1

    ledger.mark_review_hold(
        Path("Extras/Bonus.mkv"),
        hold_path=(
            tmp_path
            / "review-hold"
            / "Bonus.mkv"
        ),
        sha256="three",
    )

    assert ledger.coverage_complete is True
    assert ledger.accounted_files == 3
    assert ledger.unresolved_files == 0
    assert ledger.coverage_percent == 100


def test_unknown_snapshot_path_is_rejected(
    tmp_path: Path,
):
    ledger = SnapshotLedger.from_snapshot(
        make_snapshot(tmp_path)
    )

    with pytest.raises(
        ValueError,
        match="does not belong",
    ):
        ledger.mark_identical(
            Path("Unknown/File.mkv"),
            existing_path=(
                tmp_path
                / "library"
                / "File.mkv"
            ),
            sha256="hash",
        )


def test_entry_can_be_reclassified(
    tmp_path: Path,
):
    ledger = SnapshotLedger.from_snapshot(
        make_snapshot(tmp_path)
    )

    path = Path(
        "Extras/Bonus.mkv"
    )

    ledger.mark_unresolved(
        path,
        detail="Needs manual review",
    )

    assert (
        ledger.get(path).disposition
        is SnapshotDisposition.UNRESOLVED
    )

    ledger.mark_review_hold(
        path,
        hold_path=(
            tmp_path
            / "review-hold"
            / "Bonus.mkv"
        ),
        sha256="verified",
    )

    assert (
        ledger.get(path).disposition
        is SnapshotDisposition.REVIEW_HOLD
    )
