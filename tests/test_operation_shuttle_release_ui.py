from pathlib import Path
from unittest.mock import Mock

import deckflix_app.operations_ui as ui
from deckflix_app.operation import (
    OperationManager,
    ShuttleReleaseResult,
)


def manager_with_operation(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    (shuttle / "movie.mkv").write_bytes(
        b"media"
    )

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-UI-RELEASE-001",
    )

    return manager, shuttle


def release_result(
    *,
    emptied,
):
    return ShuttleReleaseResult(
        emptied=emptied,
        unmounted=True,
        deleted_entries=1 if emptied else 0,
        source="/dev/test1",
        filesystem="exfat",
        label="SHUTTLE",
    )


def test_empty_eject_wrong_id_never_calls_engine(
    tmp_path,
    monkeypatch,
    capsys,
):
    manager, _ = manager_with_operation(
        tmp_path
    )

    engine = Mock()

    monkeypatch.setattr(
        ui,
        "execute_empty_and_unmount",
        engine,
    )

    answers = iter([
        "1",
        "WRONG",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    ui.shuttle_release(
        manager,
        tmp_path / "state.json",
    )

    engine.assert_not_called()

    assert manager.active is True

    output = capsys.readouterr().out

    assert "CANCELLED" in output
    assert "No files have been changed." in output


def test_empty_eject_success_clears_operation(
    tmp_path,
    monkeypatch,
    capsys,
):
    manager, _ = manager_with_operation(
        tmp_path
    )

    monkeypatch.setattr(
        ui,
        "execute_empty_and_unmount",
        lambda manager, confirmation: (
            release_result(emptied=True)
        ),
    )

    delete_saved = Mock()

    monkeypatch.setattr(
        ui,
        "delete_saved_operation",
        delete_saved,
    )

    answers = iter([
        "1",
        "DF-UI-RELEASE-001",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    state = tmp_path / "state.json"

    ui.shuttle_release(
        manager,
        state,
    )

    assert manager.active is False

    delete_saved.assert_called_once_with(
        state
    )

    output = capsys.readouterr().out

    assert "Contents       EMPTY" in output
    assert "Filesystem     UNMOUNTED" in output


def test_empty_eject_failure_retains_operation(
    tmp_path,
    monkeypatch,
):
    manager, _ = manager_with_operation(
        tmp_path
    )

    def blocked(*args, **kwargs):
        raise RuntimeError(
            "simulated safety block"
        )

    monkeypatch.setattr(
        ui,
        "execute_empty_and_unmount",
        blocked,
    )

    answers = iter([
        "1",
        "DF-UI-RELEASE-001",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    ui.shuttle_release(
        manager,
        tmp_path / "state.json",
    )

    assert manager.active is True


def test_eject_only_success_preserves_release_semantics(
    tmp_path,
    monkeypatch,
    capsys,
):
    manager, _ = manager_with_operation(
        tmp_path
    )

    monkeypatch.setattr(
        ui,
        "execute_unmount_only",
        lambda manager: (
            release_result(emptied=False)
        ),
    )

    monkeypatch.setattr(
        ui,
        "delete_saved_operation",
        lambda path: None,
    )

    answers = iter([
        "2",
        "y",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    ui.shuttle_release(
        manager,
        tmp_path / "state.json",
    )

    assert manager.active is False

    output = capsys.readouterr().out

    assert "Contents       PRESERVED" in output
    assert "Filesystem     UNMOUNTED" in output


def test_eject_only_no_confirmation_does_nothing(
    tmp_path,
    monkeypatch,
):
    manager, _ = manager_with_operation(
        tmp_path
    )

    engine = Mock()

    monkeypatch.setattr(
        ui,
        "execute_unmount_only",
        engine,
    )

    answers = iter([
        "2",
        "n",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    ui.shuttle_release(
        manager,
        tmp_path / "state.json",
    )

    engine.assert_not_called()
    assert manager.active is True
