from pathlib import Path

from deckflix_app.decision import (
    ApprovalStatus,
)
from deckflix_app.operation import (
    OperationManager,
    OperationState,
    SnapshotDisposition,
    approve_ready_items,
    delete_saved_operation,
    load_operation_manager,
    manager_from_dict,
    manager_to_dict,
    prepare_operation,
    save_operation_manager,
)


SOURCE_PATH = Path(
    "1883/1883.S01E01.1080p.WEB-DL.HEVC.mkv"
)


def build_manager(
    tmp_path: Path,
) -> OperationManager:
    shuttle = (
        tmp_path
        / "shuttle"
    )

    movies = (
        tmp_path
        / "movies"
    )

    tv = (
        tmp_path
        / "tv"
    )

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    source = (
        shuttle
        / SOURCE_PATH
    )

    source.parent.mkdir()
    source.write_bytes(
        b"media"
    )

    manager = (
        OperationManager()
    )

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[
            movies
        ],
        tv_libraries=[
            tv
        ],
        operation_id=(
            "DF-PERSIST-001"
        ),
    )

    return manager


def test_save_and_restore_snapshot_ready_operation(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    destination = (
        tmp_path
        / "current-operation.json"
    )

    save_operation_manager(
        manager,
        destination,
    )

    restored = (
        load_operation_manager(
            destination
        )
    )

    assert restored.active is True

    assert (
        restored.operation.id
        == "DF-PERSIST-001"
    )

    assert (
        restored.state
        is OperationState.SNAPSHOT_READY
    )

    assert (
        restored.operation
        .snapshot
        .file_count
        == 1
    )

    assert (
        restored.decisions.total
        == 1
    )

    assert (
        restored.approval_plan.total
        == 1
    )

    assert (
        restored.approval_plan.count(
            ApprovalStatus.READY
        )
        == 1
    )


def test_save_and_restore_approved_operation(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    approve_ready_items(
        manager
    )

    destination = (
        tmp_path
        / "current-operation.json"
    )

    save_operation_manager(
        manager,
        destination,
    )

    restored = (
        load_operation_manager(
            destination
        )
    )

    assert (
        restored.state
        is OperationState.APPROVED
    )

    assert (
        restored.approval_plan.count(
            ApprovalStatus.APPROVED
        )
        == 1
    )

    assert (
        restored.approval_plan.count(
            ApprovalStatus.READY
        )
        == 0
    )


def test_restored_snapshot_can_be_validated(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    destination = (
        tmp_path
        / "current-operation.json"
    )

    save_operation_manager(
        manager,
        destination,
    )

    restored = (
        load_operation_manager(
            destination
        )
    )

    assert (
        restored.validate_snapshot()
        is True
    )


def test_restored_snapshot_detects_change(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    destination = (
        tmp_path
        / "current-operation.json"
    )

    save_operation_manager(
        manager,
        destination,
    )

    source = (
        manager.operation
        .snapshot
        .shuttle_path
    )

    (
        source
        / "changed.mkv"
    ).write_bytes(
        b"changed"
    )

    restored = (
        load_operation_manager(
            destination
        )
    )

    assert (
        restored.validate_snapshot()
        is False
    )

    assert (
        restored.state
        is OperationState.INVALIDATED
    )


def test_missing_state_returns_empty_manager(
    tmp_path: Path,
):
    restored = (
        load_operation_manager(
            tmp_path
            / "missing.json"
        )
    )

    assert (
        restored.active
        is False
    )


def test_delete_saved_operation(
    tmp_path: Path,
):
    destination = (
        tmp_path
        / "current-operation.json"
    )

    destination.write_text(
        "{}",
        encoding="utf-8",
    )

    delete_saved_operation(
        destination
    )

    assert (
        destination.exists()
        is False
    )


def test_new_operation_has_unresolved_ledger(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    ledger = (
        manager.require_ledger()
    )

    assert (
        ledger.total_files
        == 1
    )

    assert (
        ledger.unresolved_files
        == 1
    )

    assert (
        ledger.count(
            SnapshotDisposition.UNRESOLVED
        )
        == 1
    )


def test_unresolved_ledger_survives_restart(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    destination = (
        tmp_path
        / "current-operation.json"
    )

    save_operation_manager(
        manager,
        destination,
    )

    restored = (
        load_operation_manager(
            destination
        )
    )

    ledger = (
        restored.require_ledger()
    )

    entry = ledger.get(
        SOURCE_PATH
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.UNRESOLVED
    )


def test_imported_ledger_entry_survives_restart(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    manager.require_ledger().mark_imported(
        SOURCE_PATH,
        destination=(
            tmp_path
            / "movies"
            / "1883.mkv"
        ),
        sha256="imported-hash",
    )

    destination = (
        tmp_path
        / "current-operation.json"
    )

    save_operation_manager(
        manager,
        destination,
    )

    restored = (
        load_operation_manager(
            destination
        )
    )

    entry = (
        restored.require_ledger()
        .get(
            SOURCE_PATH
        )
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.IMPORTED
    )

    assert (
        entry.sha256
        == "imported-hash"
    )

    assert (
        entry.evidence_path
        == (
            tmp_path
            / "movies"
            / "1883.mkv"
        )
    )


def test_identical_ledger_entry_survives_restart(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    existing = (
        tmp_path
        / "tv"
        / "1883-existing.mkv"
    )

    manager.require_ledger().mark_identical(
        SOURCE_PATH,
        existing_path=existing,
        sha256="identical-hash",
    )

    destination = (
        tmp_path
        / "current-operation.json"
    )

    save_operation_manager(
        manager,
        destination,
    )

    restored = (
        load_operation_manager(
            destination
        )
    )

    entry = (
        restored.require_ledger()
        .get(
            SOURCE_PATH
        )
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.IDENTICAL
    )

    assert (
        entry.sha256
        == "identical-hash"
    )

    assert (
        entry.evidence_path
        == existing
    )


def test_review_hold_entry_survives_restart(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    hold = (
        tmp_path
        / "review-hold"
        / SOURCE_PATH
    )

    manager.require_ledger().mark_review_hold(
        SOURCE_PATH,
        hold_path=hold,
        sha256="hold-hash",
    )

    destination = (
        tmp_path
        / "current-operation.json"
    )

    save_operation_manager(
        manager,
        destination,
    )

    restored = (
        load_operation_manager(
            destination
        )
    )

    entry = (
        restored.require_ledger()
        .get(
            SOURCE_PATH
        )
    )

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.REVIEW_HOLD
    )

    assert (
        entry.sha256
        == "hold-hash"
    )

    assert (
        entry.evidence_path
        == hold
    )


def test_version_one_state_loads_conservatively(
    tmp_path: Path,
):
    manager = build_manager(
        tmp_path
    )

    manager.require_ledger().mark_imported(
        SOURCE_PATH,
        destination=(
            tmp_path
            / "movies"
            / "1883.mkv"
        ),
        sha256="will-not-exist-in-v1",
    )

    data = manager_to_dict(
        manager
    )

    data["version"] = 1
    data.pop(
        "ledger",
        None,
    )

    restored = (
        manager_from_dict(
            data
        )
    )

    ledger = (
        restored.require_ledger()
    )

    assert (
        ledger.total_files
        == 1
    )

    assert (
        ledger.accounted_files
        == 0
    )

    assert (
        ledger.unresolved_files
        == 1
    )

    assert (
        ledger.get(
            SOURCE_PATH
        ).disposition
        is SnapshotDisposition.UNRESOLVED
    )
