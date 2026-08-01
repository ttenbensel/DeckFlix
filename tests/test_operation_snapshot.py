from datetime import datetime
from pathlib import Path

from deckflix_app.operation import (
    OperationState,
    create_operation,
    create_shuttle_snapshot,
    snapshot_matches_current,
)


def test_snapshot_records_files_and_bytes(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    first = shuttle / "Movies" / "Alien.mkv"
    second = shuttle / "TV" / "1883.S01E01.mkv"

    first.parent.mkdir()
    second.parent.mkdir()

    first.write_bytes(b"alien")
    second.write_bytes(b"1883")

    snapshot = create_shuttle_snapshot(
        shuttle,
        created_at=datetime(2026, 8, 1, 13, 0, 0),
    )

    assert snapshot.file_count == 2
    assert snapshot.total_bytes == 9
    assert len(snapshot.fingerprint) == 64
    assert snapshot.files[0].relative_path == Path(
        "Movies/Alien.mkv"
    )


def test_operation_has_stable_supplied_id(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    operation = create_operation(
        shuttle,
        created_at=datetime(2026, 8, 1, 13, 0, 0),
        operation_id="DF-TEST-001",
    )

    assert operation.id == "DF-TEST-001"
    assert operation.state is OperationState.SNAPSHOT_READY
    assert operation.snapshot.file_count == 0


def test_snapshot_matches_unchanged_shuttle(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    file = shuttle / "movie.mkv"
    file.write_bytes(b"media")

    snapshot = create_shuttle_snapshot(shuttle)

    assert snapshot_matches_current(snapshot) is True


def test_snapshot_detects_added_file(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    (shuttle / "first.mkv").write_bytes(b"one")
    snapshot = create_shuttle_snapshot(shuttle)

    (shuttle / "second.mkv").write_bytes(b"two")

    assert snapshot_matches_current(snapshot) is False


def test_snapshot_detects_modified_file(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    file = shuttle / "movie.mkv"
    file.write_bytes(b"original")

    snapshot = create_shuttle_snapshot(shuttle)

    file.write_bytes(b"changed content")

    assert snapshot_matches_current(snapshot) is False


def test_snapshot_detects_removed_file(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    file = shuttle / "movie.mkv"
    file.write_bytes(b"media")

    snapshot = create_shuttle_snapshot(shuttle)
    file.unlink()

    assert snapshot_matches_current(snapshot) is False


def test_snapshot_ignores_sample_files(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    sample = shuttle / "Release" / "Sample" / "sample.mkv"
    real = shuttle / "Release" / "movie.mkv"

    sample.parent.mkdir(parents=True)
    sample.write_bytes(b"sample")
    real.write_bytes(b"real")

    snapshot = create_shuttle_snapshot(shuttle)

    assert snapshot.file_count == 1
    assert snapshot.files[0].relative_path == Path(
        "Release/movie.mkv"
    )
