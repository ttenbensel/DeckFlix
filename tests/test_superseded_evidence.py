from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    SnapshotDisposition,
)
from deckflix_app.operation.evidence import (
    _validate_superseded_evidence,
    validate_snapshot_evidence,
)
from deckflix_app.operation.workflow import (
    prepare_operation,
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


def _prepared_manager(
    tmp_path: Path,
):
    shuttle, movies, tv = _roots(
        tmp_path
    )

    losing = (
        shuttle
        / "Example.Show.S01E01.480p.HDTV.x264.mkv"
    )

    survivor = (
        shuttle
        / "Example.Show.S01E01.720p.WEBRip.x264.mkv"
    )

    losing.write_bytes(
        b"low"
    )

    survivor.write_bytes(
        b"this is a larger better quality survivor"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-SUPERSEDED-EVIDENCE",
    )

    ledger = manager.require_ledger()

    losing_relative = (
        losing.relative_to(shuttle)
    )

    entry = ledger.get(
        losing_relative
    )

    assert entry is not None
    assert (
        entry.disposition
        is SnapshotDisposition.SUPERSEDED
    )

    return (
        manager,
        shuttle,
        losing,
        survivor,
        ledger,
    )


def _direct_validate(
    *,
    manager: OperationManager,
    relative_path: Path,
) -> tuple[bool, str]:
    operation = manager.require_operation()
    ledger = manager.require_ledger()

    entry = ledger.get(
        relative_path
    )

    assert entry is not None

    snapshot_paths = {
        item.relative_path
        for item in operation.snapshot.files
    }

    return _validate_superseded_evidence(
        entry=entry,
        snapshot_paths=snapshot_paths,
        shuttle_path=(
            operation.snapshot.shuttle_path
        ),
    )


def test_prepare_operation_creates_superseded_without_hash_identity(
    tmp_path: Path,
):
    (
        _,
        shuttle,
        losing,
        survivor,
        ledger,
    ) = _prepared_manager(
        tmp_path
    )

    entry = ledger.get(
        losing.relative_to(shuttle)
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.SUPERSEDED
    )

    assert (
        Path(entry.evidence_path).resolve()
        == survivor.resolve()
    )

    assert entry.sha256 is None


def test_valid_superseded_survivor_passes_authoritative_evidence(
    tmp_path: Path,
):
    (
        manager,
        shuttle,
        losing,
        _,
        ledger,
    ) = _prepared_manager(
        tmp_path
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.invalid == 0
    assert result.superseded == 1

    entry = ledger.get(
        losing.relative_to(shuttle)
    )

    assert entry is not None
    assert (
        entry.disposition
        is SnapshotDisposition.SUPERSEDED
    )


def test_superseded_different_size_is_valid_when_snapshot_is_unchanged(
    tmp_path: Path,
):
    (
        manager,
        shuttle,
        losing,
        survivor,
        ledger,
    ) = _prepared_manager(
        tmp_path
    )

    assert (
        losing.stat().st_size
        != survivor.stat().st_size
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.invalid == 0
    assert result.superseded == 1

    entry = ledger.get(
        losing.relative_to(shuttle)
    )

    assert entry is not None
    assert (
        entry.disposition
        is SnapshotDisposition.SUPERSEDED
    )


def test_missing_superseded_survivor_fails_direct_evidence_check(
    tmp_path: Path,
):
    (
        manager,
        shuttle,
        losing,
        survivor,
        _,
    ) = _prepared_manager(
        tmp_path
    )

    relative = losing.relative_to(
        shuttle
    )

    survivor.unlink()

    valid, reason = _direct_validate(
        manager=manager,
        relative_path=relative,
    )

    assert valid is False
    assert "not a file" in reason.lower()


def test_external_superseded_survivor_fails_closed(
    tmp_path: Path,
):
    (
        manager,
        shuttle,
        losing,
        _,
        ledger,
    ) = _prepared_manager(
        tmp_path
    )

    external = (
        tmp_path
        / "external"
        / "Example.Show.S01E01.mkv"
    )

    external.parent.mkdir()
    external.write_bytes(
        b"external"
    )

    ledger.mark_superseded(
        losing.relative_to(shuttle),
        surviving_path=external,
    )

    valid, reason = _direct_validate(
        manager=manager,
        relative_path=(
            losing.relative_to(shuttle)
        ),
    )

    assert valid is False
    assert "outside shuttle" in reason.lower()


def test_non_snapshot_shuttle_survivor_fails_direct_evidence_check(
    tmp_path: Path,
):
    (
        manager,
        shuttle,
        losing,
        _,
        ledger,
    ) = _prepared_manager(
        tmp_path
    )

    extra = (
        shuttle
        / "Not.In.Snapshot.mkv"
    )

    extra.write_bytes(
        b"later"
    )

    ledger.mark_superseded(
        losing.relative_to(shuttle),
        surviving_path=extra,
    )

    valid, reason = _direct_validate(
        manager=manager,
        relative_path=(
            losing.relative_to(shuttle)
        ),
    )

    assert valid is False
    assert (
        "not in shuttle snapshot"
        in reason.lower()
    )


def test_superseded_sha256_identity_claim_fails_closed(
    tmp_path: Path,
):
    (
        manager,
        shuttle,
        losing,
        survivor,
        ledger,
    ) = _prepared_manager(
        tmp_path
    )

    ledger.set(
        losing.relative_to(shuttle),
        SnapshotDisposition.SUPERSEDED,
        evidence_path=survivor,
        sha256="a" * 64,
    )

    valid, reason = _direct_validate(
        manager=manager,
        relative_path=(
            losing.relative_to(shuttle)
        ),
    )

    assert valid is False
    assert (
        "must not claim sha-256 identity"
        in reason.lower()
    )


def test_changed_survivor_invalidates_immutable_snapshot(
    tmp_path: Path,
):
    (
        manager,
        _,
        _,
        survivor,
        _,
    ) = _prepared_manager(
        tmp_path
    )

    survivor.write_bytes(
        b"survivor changed after immutable snapshot"
    )

    assert manager.validate_snapshot() is False

    operation = manager.require_operation()

    assert (
        operation.state.value
        == "INVALIDATED"
    )
