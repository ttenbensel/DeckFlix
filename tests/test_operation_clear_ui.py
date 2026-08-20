from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
)
from deckflix_app.operation.ledger import (
    SnapshotDisposition,
)
import deckflix_app.operations_ui as ui


def make_shuttle(
    tmp_path: Path,
) -> Path:
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    (
        shuttle / "movie.mkv"
    ).write_bytes(b"movie")

    return shuttle


def make_manager(
    tmp_path: Path,
) -> OperationManager:
    manager = OperationManager()

    manager.begin(
        make_shuttle(tmp_path),
        operation_id="DF-TEST-CLEAR",
    )

    return manager


def test_clear_requires_exact_operation_id(
    tmp_path,
    monkeypatch,
):
    manager = make_manager(tmp_path)

    state_path = (
        tmp_path / "current-operation.json"
    )
    state_path.write_text(
        "{}",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "wrong-id",
    )

    ui.clear_operation(
        manager,
        state_path,
    )

    assert manager.active is True
    assert state_path.exists() is True


def test_clear_with_exact_id_removes_operation_state(
    tmp_path,
    monkeypatch,
):
    manager = make_manager(tmp_path)

    state_path = (
        tmp_path / "current-operation.json"
    )
    state_path.write_text(
        "{}",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "DF-TEST-CLEAR",
    )

    ui.clear_operation(
        manager,
        state_path,
    )

    assert manager.active is False
    assert state_path.exists() is False


def test_clear_blocked_when_import_authorized(
    tmp_path,
    monkeypatch,
):
    manager = make_manager(tmp_path)

    manager.decisions = object()
    manager.approval_plan = object()
    manager.approve()
    manager.authorize_import()

    state_path = (
        tmp_path / "current-operation.json"
    )
    state_path.write_text(
        "{}",
        encoding="utf-8",
    )

    def unexpected_input(_):
        raise AssertionError(
            "confirmation must not be requested"
        )

    monkeypatch.setattr(
        "builtins.input",
        unexpected_input,
    )

    ui.clear_operation(
        manager,
        state_path,
    )

    assert manager.active is True
    assert manager.import_authorized is True
    assert state_path.exists() is True


def test_clear_blocked_while_importing(
    tmp_path,
    monkeypatch,
):
    manager = make_manager(tmp_path)

    manager.decisions = object()
    manager.approval_plan = object()
    manager.approve()
    manager.authorize_import()
    manager.begin_import()

    state_path = (
        tmp_path / "current-operation.json"
    )
    state_path.write_text(
        "{}",
        encoding="utf-8",
    )

    def unexpected_input(_):
        raise AssertionError(
            "confirmation must not be requested"
        )

    monkeypatch.setattr(
        "builtins.input",
        unexpected_input,
    )

    ui.clear_operation(
        manager,
        state_path,
    )

    assert manager.active is True
    assert state_path.exists() is True


def test_clear_blocked_with_accounted_ledger(
    tmp_path,
    monkeypatch,
):
    manager = make_manager(tmp_path)
    ledger = manager.require_ledger()

    relative_path = (
        manager.require_operation()
        .snapshot.files[0]
        .relative_path
    )

    ledger.set(
        relative_path,
        SnapshotDisposition.IDENTICAL,
        evidence_path=(
            tmp_path / "existing.mkv"
        ),
        sha256="test",
    )

    state_path = (
        tmp_path / "current-operation.json"
    )
    state_path.write_text(
        "{}",
        encoding="utf-8",
    )

    def unexpected_input(_):
        raise AssertionError(
            "confirmation must not be requested"
        )

    monkeypatch.setattr(
        "builtins.input",
        unexpected_input,
    )

    ui.clear_operation(
        manager,
        state_path,
    )

    assert manager.active is True
    assert ledger.accounted_files == 1
    assert state_path.exists() is True
