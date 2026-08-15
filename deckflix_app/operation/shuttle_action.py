from dataclasses import dataclass

from .evidence import validate_snapshot_evidence
from .final_safety import (
    create_final_safety_certificate,
    final_safety_certificate_matches,
)
from .manager import OperationManager


@dataclass(frozen=True, slots=True)
class ShuttleActionPreflightResult:
    ready: bool
    reasons: tuple[str, ...]
    snapshot_files: int
    validated_files: int
    unresolved: int
    verified_bytes: int

    @property
    def status(self) -> str:
        if self.ready:
            return "READY"

        return "BLOCKED"


def run_shuttle_action_preflight(
    manager: OperationManager,
) -> ShuttleActionPreflightResult:
    """
    Perform the final non-destructive safety gate before
    any future Empty & Eject or Eject Only action.

    This function:
      - requires an existing Final Safety Certificate,
      - confirms that certificate still matches the
        current operation and ledger,
      - confirms the physical shuttle still matches the
        immutable snapshot,
      - re-runs the authoritative SHA-256 evidence audit,
      - refreshes the Final Safety Certificate only when
        the complete audit succeeds.

    No shuttle or evidence file is modified, moved,
    deleted, unmounted, or ejected.
    """
    reasons: list[str] = []

    if not manager.active:
        return ShuttleActionPreflightResult(
            ready=False,
            reasons=(
                "No shuttle operation is active",
            ),
            snapshot_files=0,
            validated_files=0,
            unresolved=0,
            verified_bytes=0,
        )

    operation = manager.require_operation()
    ledger = manager.require_ledger()

    if manager.final_safety_certificate is None:
        reasons.append(
            "Final Safety Validation has not been completed"
        )

    elif not final_safety_certificate_matches(
        manager
    ):
        manager.final_safety_certificate = None

        reasons.append(
            "Final Safety Certificate no longer matches "
            "the current operation or evidence ledger"
        )

    if reasons:
        return ShuttleActionPreflightResult(
            ready=False,
            reasons=tuple(reasons),
            snapshot_files=(
                operation.snapshot.file_count
            ),
            validated_files=0,
            unresolved=ledger.unresolved_files,
            verified_bytes=0,
        )

    try:
        manager.require_valid_snapshot()

    except Exception as exc:
        manager.final_safety_certificate = None

        return ShuttleActionPreflightResult(
            ready=False,
            reasons=(
                f"Shuttle snapshot validation failed: {exc}",
            ),
            snapshot_files=(
                operation.snapshot.file_count
            ),
            validated_files=0,
            unresolved=ledger.unresolved_files,
            verified_bytes=0,
        )

    # Withdraw the old certificate before performing the
    # authoritative current evidence audit.
    manager.final_safety_certificate = None

    try:
        evidence = validate_snapshot_evidence(
            manager
        )

    except Exception as exc:
        return ShuttleActionPreflightResult(
            ready=False,
            reasons=(
                f"Evidence validation failed: {exc}",
            ),
            snapshot_files=(
                operation.snapshot.file_count
            ),
            validated_files=0,
            unresolved=ledger.unresolved_files,
            verified_bytes=0,
        )

    if not evidence.safe:
        reasons.append(
            "Current SHA-256 evidence does not cover "
            "the complete shuttle snapshot"
        )

    if evidence.invalid:
        reasons.append(
            f"{evidence.invalid} evidence file(s) "
            "failed validation"
        )

    if evidence.unresolved:
        reasons.append(
            f"{evidence.unresolved} shuttle snapshot "
            "file(s) remain unresolved"
        )

    if reasons:
        return ShuttleActionPreflightResult(
            ready=False,
            reasons=tuple(reasons),
            snapshot_files=evidence.total,
            validated_files=evidence.valid,
            unresolved=evidence.unresolved,
            verified_bytes=evidence.verified_bytes,
        )

    # A completely successful immediate revalidation
    # refreshes the certificate.
    create_final_safety_certificate(
        manager,
        evidence,
    )

    return ShuttleActionPreflightResult(
        ready=True,
        reasons=(),
        snapshot_files=evidence.total,
        validated_files=evidence.valid,
        unresolved=evidence.unresolved,
        verified_bytes=evidence.verified_bytes,
    )
