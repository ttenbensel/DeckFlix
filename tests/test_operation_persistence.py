from pathlib import Path

from deckflix_app.decision import (
    ApprovalStatus,
)
from deckflix_app.operation import (
    OperationManager,
    OperationState,
    approve_ready_items,
    delete_saved_operation,
    load_operation_manager,
    prepare_operation,
    save_operation_manager,
)


def build_manager(tmp_path: Path) -> OperationManager:
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    source = (
        shuttle
        / "1883"
        / "1883.S01E01.1080p.WEB-DL.HEVC.mkv"
    )
    source.parent.mkdir()
    source.write_bytes(b"media")

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-PERSIST-001",
    )

    return manager


def test_save_and_restore_snapshot_ready_operation(
    tmp_path: Path,
):
    manager = build_manager(tmp_path)
    destination = tmp_path / "current-operation.json"

    save_operation_manager(manager, destination)
    restored = load_operation_manager(destination)

    assert restored.active is True
    assert restored.operation.id == "DF-PERSIST-001"
    assert restored.state is OperationState.SNAPSHOT_READY
    assert restored.operation.snapshot.file_count == 1
    assert restored.decisions.total == 1
    assert restored.approval_plan.total == 1
    assert (
        restored.approval_plan.count(
            ApprovalStatus.READY
        )
        == 1
    )


def test_save_and_restore_approved_operation(
    tmp_path: Path,
):
    manager = build_manager(tmp_path)
    approve_ready_items(manager)

    destination = tmp_path / "current-operation.json"
    save_operation_manager(manager, destination)

    restored = load_operation_manager(destination)

    assert restored.state is OperationState.APPROVED
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
    manager = build_manager(tmp_path)
    destination = tmp_path / "current-operation.json"

    save_operation_manager(manager, destination)
    restored = load_operation_manager(destination)

    assert restored.validate_snapshot() is True


def test_restored_snapshot_detects_change(
    tmp_path: Path,
):
    manager = build_manager(tmp_path)
    destination = tmp_path / "current-operation.json"

    save_operation_manager(manager, destination)

    source = manager.operation.snapshot.shuttle_path
    (source / "changed.mkv").write_bytes(b"changed")

    restored = load_operation_manager(destination)

    assert restored.validate_snapshot() is False
    assert restored.state is OperationState.INVALIDATED


def test_missing_state_returns_empty_manager(
    tmp_path: Path,
):
    restored = load_operation_manager(
        tmp_path / "missing.json"
    )

    assert restored.active is False


def test_delete_saved_operation(tmp_path: Path):
    destination = tmp_path / "current-operation.json"
    destination.write_text("{}", encoding="utf-8")

    delete_saved_operation(destination)

    assert destination.exists() is False
