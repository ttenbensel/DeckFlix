from pathlib import Path

import pytest

from deckflix_app.operation import (
    InvalidOperationTransition,
    OperationInvalidated,
    OperationManager,
    OperationState,
)


def make_shuttle(tmp_path: Path) -> Path:
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()
    (shuttle / "movie.mkv").write_bytes(b"media")
    return shuttle


def test_manager_begins_operation(tmp_path: Path):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()

    operation = manager.begin(
        shuttle,
        operation_id="DF-TEST-001",
    )

    assert manager.active is True
    assert manager.state is OperationState.SNAPSHOT_READY
    assert operation.id == "DF-TEST-001"
    assert operation.snapshot.file_count == 1


def test_manager_rejects_second_active_operation(
    tmp_path: Path,
):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()
    manager.begin(shuttle)

    with pytest.raises(
        InvalidOperationTransition,
        match="already active",
    ):
        manager.begin(shuttle)


def test_manager_attaches_decisions_and_approval(
    tmp_path: Path,
):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()
    manager.begin(shuttle)

    decisions = object()
    approval = object()

    manager.attach_decisions(decisions)
    manager.attach_approval_plan(approval)

    assert manager.decisions is decisions
    assert manager.approval_plan is approval


def test_manager_requires_decisions_before_approval_plan(
    tmp_path: Path,
):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()
    manager.begin(shuttle)

    with pytest.raises(
        InvalidOperationTransition,
        match="Decisions",
    ):
        manager.attach_approval_plan(object())


def test_manager_approves_valid_operation(tmp_path: Path):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()
    manager.begin(shuttle)
    manager.attach_decisions(object())
    manager.attach_approval_plan(object())

    manager.approve()

    assert manager.state is OperationState.APPROVED


def test_manager_moves_through_import_to_complete(
    tmp_path: Path,
):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()
    manager.begin(shuttle)
    manager.attach_decisions(object())
    manager.attach_approval_plan(object())
    manager.approve()

    manager.begin_import()

    assert manager.state is OperationState.IMPORTING

    result = object()
    certificate = object()

    manager.complete(
        import_result=result,
        certificate=certificate,
    )

    assert manager.state is OperationState.COMPLETE
    assert manager.import_result is result
    assert manager.certificate is certificate


def test_manager_invalidates_changed_shuttle(
    tmp_path: Path,
):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()
    manager.begin(shuttle)

    (shuttle / "new-file.mkv").write_bytes(b"changed")

    assert manager.validate_snapshot() is False
    assert manager.state is OperationState.INVALIDATED


def test_manager_blocks_decisions_after_change(
    tmp_path: Path,
):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()
    manager.begin(shuttle)

    (shuttle / "movie.mkv").write_bytes(
        b"changed content"
    )

    with pytest.raises(OperationInvalidated):
        manager.attach_decisions(object())

    assert manager.state is OperationState.INVALIDATED


def test_manager_clear_resets_all_state(tmp_path: Path):
    shuttle = make_shuttle(tmp_path)
    manager = OperationManager()
    manager.begin(shuttle)
    manager.attach_decisions(object())
    manager.attach_approval_plan(object())

    manager.clear()

    assert manager.active is False
    assert manager.state is None
    assert manager.decisions is None
    assert manager.approval_plan is None
