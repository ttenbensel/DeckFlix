from datetime import datetime
from pathlib import Path

from deckflix_app.importer.safety import (
    ShuttleSafetyChecker,
    ShuttleSafetyResult,
)
from deckflix_app.operation import (
    OperationManager,
    create_final_safety_certificate,
    manager_from_dict,
    manager_to_dict,
    validate_snapshot_evidence,
)
from deckflix_app.operation.evidence import (
    file_sha256,
)
from deckflix_app.operation.final_safety import (
    final_safety_certificate_matches,
)
from deckflix_app.operation.ledger import (
    SnapshotDisposition,
)


def build_superseded_manager(
    tmp_path: Path,
) -> OperationManager:
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    losing = (
        shuttle
        / "old.mkv"
    )

    survivor = (
        shuttle
        / "new.mkv"
    )

    losing.write_bytes(
        b"old"
    )

    survivor.write_bytes(
        b"better-media"
    )

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id=(
            "DF-SUPERSEDED-CERT-001"
        ),
    )

    ledger = manager.require_ledger()

    ledger.mark_superseded(
        Path("old.mkv"),
        surviving_path=survivor,
        detail=(
            "Logical media represented by "
            "surviving snapshot candidate"
        ),
    )

    review_hold = (
        tmp_path
        / "review-hold"
        / "new.mkv"
    )

    review_hold.parent.mkdir(
        parents=True
    )

    review_hold.write_bytes(
        survivor.read_bytes()
    )

    ledger.mark_review_hold(
        Path("new.mkv"),
        hold_path=review_hold,
        sha256=file_sha256(
            review_hold
        ),
    )

    return manager


def test_final_certificate_records_superseded(
    tmp_path: Path,
):
    manager = (
        build_superseded_manager(
            tmp_path
        )
    )

    result = (
        validate_snapshot_evidence(
            manager
        )
    )

    assert result.safe is True
    assert result.total == 2
    assert result.valid == 2
    assert result.superseded == 1
    assert result.review_hold == 1
    assert result.unresolved == 0

    certificate = (
        create_final_safety_certificate(
            manager,
            result,
            validated_at=datetime(
                2026,
                8,
                22,
                12,
                0,
                0,
            ),
        )
    )

    assert (
        certificate.snapshot_files
        == 2
    )

    assert (
        certificate.superseded
        == 1
    )

    assert (
        certificate.review_hold
        == 1
    )

    assert (
        certificate.unresolved
        == 0
    )

    assert (
        final_safety_certificate_matches(
            manager
        )
        is True
    )


def test_superseded_certificate_persists(
    tmp_path: Path,
):
    manager = (
        build_superseded_manager(
            tmp_path
        )
    )

    result = (
        validate_snapshot_evidence(
            manager
        )
    )

    create_final_safety_certificate(
        manager,
        result,
    )

    data = manager_to_dict(
        manager
    )

    certificate_data = data[
        "final_safety_certificate"
    ]

    assert (
        certificate_data[
            "superseded"
        ]
        == 1
    )

    restored = manager_from_dict(
        data
    )

    certificate = (
        restored
        .final_safety_certificate
    )

    assert certificate is not None
    assert certificate.superseded == 1

    assert (
        final_safety_certificate_matches(
            restored
        )
        is True
    )


def test_legacy_certificate_defaults_superseded_zero(
    tmp_path: Path,
):
    manager = (
        build_superseded_manager(
            tmp_path
        )
    )

    result = (
        validate_snapshot_evidence(
            manager
        )
    )

    create_final_safety_certificate(
        manager,
        result,
    )

    data = manager_to_dict(
        manager
    )

    data[
        "final_safety_certificate"
    ].pop(
        "superseded"
    )

    restored = manager_from_dict(
        data
    )

    certificate = (
        restored
        .final_safety_certificate
    )

    assert certificate is not None
    assert certificate.superseded == 0


def test_shuttle_safety_counts_superseded(
    tmp_path: Path,
):
    manager = (
        build_superseded_manager(
            tmp_path
        )
    )

    ledger = (
        manager.require_ledger()
    )

    safety = ShuttleSafetyResult(
        safe=True
    )

    checker = (
        ShuttleSafetyChecker()
    )

    checker.apply_snapshot_coverage(
        safety,
        ledger=ledger,
        required=True,
    )

    assert (
        safety.snapshot_files
        == 2
    )

    assert (
        safety.snapshot_accounted
        == 2
    )

    assert (
        safety.snapshot_unresolved
        == 0
    )

    assert (
        safety.snapshot_superseded
        == 1
    )

    assert (
        safety.snapshot_review_hold
        == 1
    )

    assert (
        safety.snapshot_coverage_complete
        is True
    )

    assert safety.safe is True


def test_superseded_has_no_sha_identity_claim(
    tmp_path: Path,
):
    manager = (
        build_superseded_manager(
            tmp_path
        )
    )

    ledger = (
        manager.require_ledger()
    )

    entry = ledger.entries[
        Path("old.mkv")
    ]

    assert (
        entry.disposition
        is SnapshotDisposition.SUPERSEDED
    )

    assert entry.sha256 is None
