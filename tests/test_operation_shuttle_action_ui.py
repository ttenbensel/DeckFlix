from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    create_final_safety_certificate,
    validate_snapshot_evidence,
)
from deckflix_app.operations_ui import (
    empty_and_eject_preflight,
)


def build_certified_manager(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    source = shuttle / "movie.mkv"
    source.write_bytes(b"media")

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-EJECT-UI-001",
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

    validation = validate_snapshot_evidence(
        manager
    )

    assert validation.safe is True

    create_final_safety_certificate(
        manager,
        validation,
    )

    return manager, evidence


def test_empty_eject_preflight_ready_screen(
    tmp_path: Path,
    capsys,
):
    manager, _ = build_certified_manager(
        tmp_path
    )

    state = tmp_path / "operation.json"

    empty_and_eject_preflight(
        manager,
        state,
    )

    output = capsys.readouterr().out

    assert "Empty & Eject" in output
    assert "Certificate         VALID" in output
    assert "Snapshot            VALID" in output
    assert "Evidence            VERIFIED" in output
    assert "Status              READY" in output

    assert (
        "Actual Empty & Eject is not enabled yet."
        in output
    )

    assert state.exists()


def test_empty_eject_preflight_blocks_changed_evidence(
    tmp_path: Path,
    capsys,
):
    manager, evidence = build_certified_manager(
        tmp_path
    )

    state = tmp_path / "operation.json"

    # Same-size external corruption.
    evidence.write_bytes(b"xxxxx")

    empty_and_eject_preflight(
        manager,
        state,
    )

    output = capsys.readouterr().out

    assert "Status              BLOCKED" in output
    assert "Blocking Reasons" in output

    assert (
        manager.final_safety_certificate
        is None
    )

    assert (
        "Actual Empty & Eject is not enabled yet."
        in output
    )


def test_empty_eject_preflight_without_operation(
    tmp_path: Path,
    capsys,
):
    manager = OperationManager()

    empty_and_eject_preflight(
        manager,
        tmp_path / "operation.json",
    )

    output = capsys.readouterr().out

    assert "No operation is active." in output
    assert "Status              BLOCKED" in output
