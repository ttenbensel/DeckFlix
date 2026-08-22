from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from .evidence import EvidenceValidationResult
from .ledger import SnapshotLedger
from .manager import OperationManager


@dataclass(frozen=True, slots=True)
class FinalSafetyCertificate:
    operation_id: str
    snapshot_fingerprint: str
    snapshot_device_id: int
    evidence_fingerprint: str
    snapshot_files: int
    imported: int
    identical: int
    superseded: int
    review_hold: int
    unresolved: int
    validated_at: datetime


def evidence_fingerprint(
    ledger: SnapshotLedger,
) -> str:
    """
    Fingerprint the complete disposition/evidence state.

    This intentionally contains no file contents. The expensive
    content verification has already been performed by
    validate_snapshot_evidence().

    Any subsequent change to disposition, evidence path,
    recorded SHA-256, or detail changes this fingerprint.
    """
    digest = sha256()

    for entry in sorted(
        ledger.entries.values(),
        key=lambda item: (
            item.relative_path
            .as_posix()
            .casefold()
        ),
    ):
        fields = (
            entry.relative_path.as_posix(),
            entry.disposition.value,
            (
                str(entry.evidence_path)
                if entry.evidence_path is not None
                else ""
            ),
            entry.sha256 or "",
            entry.detail or "",
        )

        for value in fields:
            digest.update(
                value.encode("utf-8")
            )
            digest.update(b"\0")

        digest.update(b"\n")

    return digest.hexdigest()


def create_final_safety_certificate(
    manager: OperationManager,
    result: EvidenceValidationResult,
    *,
    validated_at: datetime | None = None,
) -> FinalSafetyCertificate:
    """
    Create a certificate only from a successful authoritative
    evidence validation.
    """
    if not result.safe:
        raise ValueError(
            "Cannot certify an unsafe snapshot"
        )

    manager.require_valid_snapshot()

    operation = manager.require_operation()
    ledger = manager.require_ledger()

    if result.total != operation.snapshot.file_count:
        raise ValueError(
            "Evidence result does not match snapshot file count"
        )

    if result.valid != result.total:
        raise ValueError(
            "Evidence result does not cover every snapshot file"
        )

    if result.unresolved != 0:
        raise ValueError(
            "Cannot certify unresolved snapshot files"
        )

    certificate = FinalSafetyCertificate(
        operation_id=operation.id,
        snapshot_fingerprint=(
            operation.snapshot.fingerprint
        ),
        snapshot_device_id=(
            operation.snapshot.device_id
        ),
        evidence_fingerprint=(
            evidence_fingerprint(ledger)
        ),
        snapshot_files=(
            operation.snapshot.file_count
        ),
        imported=result.imported,
        identical=result.identical,
        superseded=result.superseded,
        review_hold=result.review_hold,
        unresolved=result.unresolved,
        validated_at=(
            validated_at or datetime.now()
        ),
    )

    manager.final_safety_certificate = certificate

    return certificate


def final_safety_certificate_matches(
    manager: OperationManager,
) -> bool:
    """
    Fast fail-closed certificate check.

    This does not re-hash evidence files. It proves that the
    current operation, snapshot identity, and recorded evidence
    state are exactly those that were certified.
    """
    certificate = (
        manager.final_safety_certificate
    )

    if certificate is None:
        return False

    if not manager.active:
        return False

    try:
        manager.require_valid_snapshot()
        operation = manager.require_operation()
        ledger = manager.require_ledger()
    except Exception:
        return False

    snapshot = operation.snapshot

    if certificate.operation_id != operation.id:
        return False

    if (
        certificate.snapshot_fingerprint
        != snapshot.fingerprint
    ):
        return False

    if (
        certificate.snapshot_device_id
        != snapshot.device_id
    ):
        return False

    if (
        certificate.snapshot_files
        != snapshot.file_count
    ):
        return False

    if ledger.unresolved_files != 0:
        return False

    if ledger.accounted_files != ledger.total_files:
        return False

    if (
        certificate.evidence_fingerprint
        != evidence_fingerprint(ledger)
    ):
        return False

    return True
