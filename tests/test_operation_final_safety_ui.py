from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
)
from deckflix_app.operations_ui import (
    final_snapshot_safety_validation,
)


def build_accounted_manager(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    source = shuttle / "movie.mkv"
    source.write_bytes(b"media")

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-SAFETY-UI-001",
    )

    evidence = (
        tmp_path
        / "library"
        / "movie.mkv"
    )

    evidence.parent.mkdir()
    evidence.write_bytes(b"media")

    from deckflix_app.operation.evidence import (
        file_sha256,
    )

    manager.require_ledger().mark_imported(
        Path("movie.mkv"),
        destination=evidence,
        sha256=file_sha256(evidence),
    )

    return manager, evidence


def test_final_validation_issues_certificate(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    manager, _ = build_accounted_manager(
        tmp_path
    )

    state = tmp_path / "operation.json"

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "y",
    )

    final_snapshot_safety_validation(
        manager,
        state,
    )

    output = capsys.readouterr().out

    assert "SAFE TO EMPTY" in output
    assert "Final Safety Certificate" in output

    assert (
        manager.final_safety_certificate
        is not None
    )

    assert state.exists()


def test_failed_revalidation_withdraws_old_certificate(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    manager, evidence = build_accounted_manager(
        tmp_path
    )

    state = tmp_path / "operation.json"

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "y",
    )

    final_snapshot_safety_validation(
        manager,
        state,
    )

    assert (
        manager.final_safety_certificate
        is not None
    )

    # Same-size corruption after certification.
    evidence.write_bytes(b"xxxxx")

    final_snapshot_safety_validation(
        manager,
        state,
    )

    capsys.readouterr()

    assert (
        manager.final_safety_certificate
        is None
    )

    assert (
        manager.require_ledger()
        .unresolved_files
        == 1
    )
