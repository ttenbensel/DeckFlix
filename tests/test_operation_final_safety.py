from datetime import datetime
from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    create_final_safety_certificate,
    final_safety_certificate_matches,
    load_operation_manager,
    manager_from_dict,
    manager_to_dict,
    save_operation_manager,
    validate_snapshot_evidence,
)


def certified_manager(
    tmp_path: Path,
) -> tuple[
    OperationManager,
    Path,
]:
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    source = shuttle / "movie.mkv"
    source.write_bytes(b"media")

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-SAFETY-001",
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

    result = validate_snapshot_evidence(
        manager
    )

    assert result.safe is True

    create_final_safety_certificate(
        manager,
        result,
        validated_at=datetime(
            2026,
            8,
            12,
            12,
            0,
            0,
        ),
    )

    return manager, evidence


def test_safe_validation_creates_matching_certificate(
    tmp_path: Path,
):
    manager, _ = certified_manager(
        tmp_path
    )

    certificate = (
        manager.final_safety_certificate
    )

    assert certificate is not None
    assert (
        certificate.operation_id
        == "DF-SAFETY-001"
    )
    assert certificate.snapshot_files == 1
    assert certificate.imported == 1
    assert certificate.unresolved == 0

    assert (
        final_safety_certificate_matches(
            manager
        )
        is True
    )


def test_certificate_fails_when_ledger_changes(
    tmp_path: Path,
):
    manager, evidence = certified_manager(
        tmp_path
    )

    manager.require_ledger().mark_imported(
        Path("movie.mkv"),
        destination=evidence,
        sha256="0" * 64,
    )

    assert (
        final_safety_certificate_matches(
            manager
        )
        is False
    )


def test_certificate_fails_when_snapshot_changes(
    tmp_path: Path,
):
    manager, _ = certified_manager(
        tmp_path
    )

    shuttle = (
        manager.require_operation()
        .snapshot
        .shuttle_path
    )

    (
        shuttle
        / "changed.mkv"
    ).write_bytes(b"changed")

    assert (
        final_safety_certificate_matches(
            manager
        )
        is False
    )


def test_certificate_survives_restart(
    tmp_path: Path,
):
    manager, _ = certified_manager(
        tmp_path
    )

    state = (
        tmp_path
        / "operation.json"
    )

    save_operation_manager(
        manager,
        state,
    )

    restored = load_operation_manager(
        state
    )

    assert (
        restored.final_safety_certificate
        is not None
    )

    assert (
        final_safety_certificate_matches(
            restored
        )
        is True
    )


def test_version_two_state_has_no_certificate(
    tmp_path: Path,
):
    manager, _ = certified_manager(
        tmp_path
    )

    data = manager_to_dict(
        manager
    )

    data["version"] = 2

    data.pop(
        "final_safety_certificate",
        None,
    )

    restored = manager_from_dict(
        data
    )

    assert (
        restored.final_safety_certificate
        is None
    )

    assert (
        final_safety_certificate_matches(
            restored
        )
        is False
    )


def test_unsafe_result_cannot_be_certified(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    (
        shuttle
        / "movie.mkv"
    ).write_bytes(b"media")

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-SAFETY-UNSAFE",
    )

    result = validate_snapshot_evidence(
        manager
    )

    assert result.safe is False

    try:
        create_final_safety_certificate(
            manager,
            result,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Unsafe result was certified"
        )

    assert (
        manager.final_safety_certificate
        is None
    )
