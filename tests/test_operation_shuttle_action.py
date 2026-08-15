from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    create_final_safety_certificate,
    run_shuttle_action_preflight,
    validate_snapshot_evidence,
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
        operation_id="DF-SHUTTLE-ACTION-001",
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

    validation = (
        validate_snapshot_evidence(
            manager
        )
    )

    assert validation.safe is True

    create_final_safety_certificate(
        manager,
        validation,
    )

    return (
        manager,
        shuttle,
        evidence,
    )


def test_certified_operation_passes_preflight(
    tmp_path: Path,
):
    manager, _, _ = (
        build_certified_manager(
            tmp_path
        )
    )

    result = (
        run_shuttle_action_preflight(
            manager
        )
    )

    assert result.ready is True
    assert result.status == "READY"
    assert result.snapshot_files == 1
    assert result.validated_files == 1
    assert result.unresolved == 0
    assert result.reasons == ()

    assert (
        manager.final_safety_certificate
        is not None
    )


def test_missing_certificate_blocks_preflight(
    tmp_path: Path,
):
    manager, _, _ = (
        build_certified_manager(
            tmp_path
        )
    )

    manager.final_safety_certificate = None

    result = (
        run_shuttle_action_preflight(
            manager
        )
    )

    assert result.ready is False
    assert result.status == "BLOCKED"

    assert any(
        "Final Safety Validation"
        in reason
        for reason in result.reasons
    )


def test_changed_ledger_blocks_preflight(
    tmp_path: Path,
):
    manager, _, evidence = (
        build_certified_manager(
            tmp_path
        )
    )

    manager.require_ledger().mark_imported(
        Path("movie.mkv"),
        destination=evidence,
        sha256="0" * 64,
    )

    result = (
        run_shuttle_action_preflight(
            manager
        )
    )

    assert result.ready is False

    assert any(
        "Certificate"
        in reason
        for reason in result.reasons
    )


def test_changed_shuttle_blocks_preflight(
    tmp_path: Path,
):
    manager, shuttle, _ = (
        build_certified_manager(
            tmp_path
        )
    )

    (
        shuttle
        / "changed.mkv"
    ).write_bytes(
        b"changed"
    )

    result = (
        run_shuttle_action_preflight(
            manager
        )
    )

    assert result.ready is False

    assert (
        manager.final_safety_certificate
        is None
    )


def test_evidence_changed_after_certificate_blocks_preflight(
    tmp_path: Path,
):
    manager, _, evidence = (
        build_certified_manager(
            tmp_path
        )
    )

    # Same size, different data. The ledger itself is
    # unchanged, so only the immediate SHA-256 audit can
    # catch this.
    evidence.write_bytes(
        b"xxxxx"
    )

    result = (
        run_shuttle_action_preflight(
            manager
        )
    )

    assert result.ready is False
    assert result.validated_files == 0
    assert result.unresolved == 1

    assert (
        manager.final_safety_certificate
        is None
    )


def test_no_active_operation_is_blocked():
    manager = OperationManager()

    result = (
        run_shuttle_action_preflight(
            manager
        )
    )

    assert result.ready is False
    assert result.snapshot_files == 0

    assert any(
        "No shuttle operation"
        in reason
        for reason in result.reasons
    )
