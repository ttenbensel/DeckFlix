from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    SnapshotDisposition,
    preserve_unresolved_in_review_hold,
)


def make_manager(
    tmp_path: Path,
    files: dict[str, bytes],
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    for name, data in files.items():
        path = shuttle / name
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(data)

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-REVIEW-HOLD-001",
    )

    return manager, shuttle


def test_preserves_unresolved_file(
    tmp_path: Path,
):
    manager, shuttle = make_manager(
        tmp_path,
        {
            "TV/Show/episode.mkv": (
                b"review-data"
            ),
        },
    )

    hold = tmp_path / "review-hold"

    result = (
        preserve_unresolved_in_review_hold(
            manager,
            review_hold_directory=hold,
        )
    )

    assert result.total == 1
    assert result.completed == 1
    assert result.resumed == 0
    assert result.failed == 0
    assert result.verified_bytes == 11

    destination = (
        hold
        / "DF-REVIEW-HOLD-001"
        / "TV/Show/episode.mkv"
    )

    assert destination.read_bytes() == (
        b"review-data"
    )

    # Review Hold never removes the shuttle source.
    assert (
        shuttle
        / "TV/Show/episode.mkv"
    ).exists()

    entry = (
        manager.require_ledger()
        .get(
            Path(
                "TV/Show/episode.mkv"
            )
        )
    )

    assert entry is not None
    assert (
        entry.disposition
        is SnapshotDisposition.REVIEW_HOLD
    )
    assert (
        entry.evidence_path
        == destination.resolve()
    )
    assert entry.sha256 is not None
    assert len(entry.sha256) == 64


def test_preserves_relative_directory_structure(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "A/B/C/movie.mkv": b"abc",
        },
    )

    hold = tmp_path / "hold"

    preserve_unresolved_in_review_hold(
        manager,
        review_hold_directory=hold,
    )

    assert (
        hold
        / "DF-REVIEW-HOLD-001"
        / "A/B/C/movie.mkv"
    ).read_bytes() == b"abc"


def test_only_unresolved_files_are_copied(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "one.mkv": b"one",
            "two.mkv": b"two",
        },
    )

    ledger = manager.require_ledger()

    ledger.mark_imported(
        Path("one.mkv"),
        destination=(
            tmp_path / "library/one.mkv"
        ),
        sha256="1" * 64,
    )

    hold = tmp_path / "hold"

    result = (
        preserve_unresolved_in_review_hold(
            manager,
            review_hold_directory=hold,
        )
    )

    assert result.total == 1
    assert result.completed == 1

    assert not (
        hold
        / "DF-REVIEW-HOLD-001"
        / "one.mkv"
    ).exists()

    assert (
        hold
        / "DF-REVIEW-HOLD-001"
        / "two.mkv"
    ).exists()


def test_existing_matching_copy_is_resumed(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "movie.mkv": b"same-data",
        },
    )

    hold = tmp_path / "hold"

    destination = (
        hold
        / "DF-REVIEW-HOLD-001"
        / "movie.mkv"
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_bytes(
        b"same-data"
    )

    result = (
        preserve_unresolved_in_review_hold(
            manager,
            review_hold_directory=hold,
        )
    )

    assert result.total == 1
    assert result.completed == 1
    assert result.resumed == 1
    assert result.failed == 0

    entry = (
        manager.require_ledger()
        .get(Path("movie.mkv"))
    )

    assert (
        entry.disposition
        is SnapshotDisposition.REVIEW_HOLD
    )


def test_existing_wrong_copy_is_replaced(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "movie.mkv": b"correct",
        },
    )

    hold = tmp_path / "hold"

    destination = (
        hold
        / "DF-REVIEW-HOLD-001"
        / "movie.mkv"
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_bytes(
        b"wrong"
    )

    result = (
        preserve_unresolved_in_review_hold(
            manager,
            review_hold_directory=hold,
        )
    )

    assert result.completed == 1
    assert result.resumed == 0
    assert result.failed == 0

    assert destination.read_bytes() == (
        b"correct"
    )


def test_second_run_has_no_unresolved_work(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "movie.mkv": b"same-data",
        },
    )

    hold = tmp_path / "hold"

    first = (
        preserve_unresolved_in_review_hold(
            manager,
            review_hold_directory=hold,
        )
    )

    assert first.completed == 1

    second = (
        preserve_unresolved_in_review_hold(
            manager,
            review_hold_directory=hold,
        )
    )

    assert second.total == 0
    assert second.completed == 0
    assert second.failed == 0


def test_progress_is_reported(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "one.mkv": b"one",
            "two.mkv": b"two",
        },
    )

    events = []

    result = (
        preserve_unresolved_in_review_hold(
            manager,
            review_hold_directory=(
                tmp_path / "hold"
            ),
            progress=events.append,
        )
    )

    assert result.completed == 2
    assert len(events) == 2

    assert events[-1].current == 2
    assert events[-1].total == 2
    assert events[-1].completed == 2
    assert events[-1].failed == 0


def test_invalid_snapshot_blocks_review_hold(
    tmp_path: Path,
):
    manager, shuttle = make_manager(
        tmp_path,
        {
            "movie.mkv": b"original",
        },
    )

    (
        shuttle
        / "movie.mkv"
    ).write_bytes(
        b"changed-after-snapshot"
    )

    hold = tmp_path / "hold"

    try:
        preserve_unresolved_in_review_hold(
            manager,
            review_hold_directory=hold,
        )
    except Exception:
        pass
    else:
        raise AssertionError(
            "Invalid snapshot was not rejected"
        )

    assert not hold.exists()

    assert (
        manager.require_ledger()
        .get(Path("movie.mkv"))
        .disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_valid_review_hold_evidence_remains_accounted(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "movie.mkv": b"review-data",
        },
    )

    hold = tmp_path / "hold"

    preserve_unresolved_in_review_hold(
        manager,
        review_hold_directory=hold,
    )

    from deckflix_app.operation import (
        validate_review_hold_evidence,
    )

    result = validate_review_hold_evidence(
        manager
    )

    assert result.checked == 1
    assert result.valid == 1
    assert result.invalid == 0
    assert result.verified_bytes == 11

    assert (
        manager.require_ledger()
        .get(Path("movie.mkv"))
        .disposition
        is SnapshotDisposition.REVIEW_HOLD
    )


def test_missing_review_hold_copy_becomes_unresolved(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "movie.mkv": b"review-data",
        },
    )

    hold = tmp_path / "hold"

    preserve_unresolved_in_review_hold(
        manager,
        review_hold_directory=hold,
    )

    destination = (
        hold
        / "DF-REVIEW-HOLD-001"
        / "movie.mkv"
    )

    destination.unlink()

    from deckflix_app.operation import (
        validate_review_hold_evidence,
    )

    result = validate_review_hold_evidence(
        manager
    )

    assert result.checked == 1
    assert result.valid == 0
    assert result.invalid == 1

    entry = (
        manager.require_ledger()
        .get(Path("movie.mkv"))
    )

    assert entry is not None
    assert (
        entry.disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_damaged_review_hold_copy_becomes_unresolved(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "movie.mkv": b"review-data",
        },
    )

    hold = tmp_path / "hold"

    preserve_unresolved_in_review_hold(
        manager,
        review_hold_directory=hold,
    )

    destination = (
        hold
        / "DF-REVIEW-HOLD-001"
        / "movie.mkv"
    )

    # Same size, different bytes. This proves size alone
    # cannot preserve REVIEW_HOLD evidence.
    destination.write_bytes(
        b"Review-data"
    )

    from deckflix_app.operation import (
        validate_review_hold_evidence,
    )

    result = validate_review_hold_evidence(
        manager
    )

    assert result.checked == 1
    assert result.valid == 0
    assert result.invalid == 1

    assert (
        manager.require_ledger()
        .get(Path("movie.mkv"))
        .disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_invalid_saved_review_hold_hash_becomes_unresolved(
    tmp_path: Path,
):
    manager, _ = make_manager(
        tmp_path,
        {
            "movie.mkv": b"review-data",
        },
    )

    hold = tmp_path / "hold"

    preserve_unresolved_in_review_hold(
        manager,
        review_hold_directory=hold,
    )

    ledger = manager.require_ledger()

    entry = ledger.get(
        Path("movie.mkv")
    )

    assert entry is not None
    assert entry.evidence_path is not None

    ledger.set(
        Path("movie.mkv"),
        SnapshotDisposition.REVIEW_HOLD,
        evidence_path=entry.evidence_path,
        sha256="0" * 64,
    )

    from deckflix_app.operation import (
        validate_review_hold_evidence,
    )

    result = validate_review_hold_evidence(
        manager
    )

    assert result.invalid == 1

    assert (
        ledger.get(Path("movie.mkv"))
        .disposition
        is SnapshotDisposition.UNRESOLVED
    )
