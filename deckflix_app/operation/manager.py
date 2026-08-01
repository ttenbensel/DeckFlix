from dataclasses import replace
from pathlib import Path
from typing import Any

from .models import Operation, OperationState
from .snapshot import (
    create_operation,
    snapshot_matches_current,
)


class InvalidOperationTransition(RuntimeError):
    pass


class OperationInvalidated(RuntimeError):
    pass


class OperationManager:
    """
    Own one DeckFlix shuttle operation.

    This is the single in-memory source of truth for the current
    snapshot, decisions, approval plan, import result, and certificate.
    """

    def __init__(self) -> None:
        self.operation: Operation | None = None
        self.decisions: Any | None = None
        self.approval_plan: Any | None = None
        self.import_result: Any | None = None
        self.certificate: Any | None = None

    @property
    def active(self) -> bool:
        return self.operation is not None

    @property
    def state(self) -> OperationState | None:
        if self.operation is None:
            return None

        return self.operation.state

    def begin(
        self,
        shuttle_path: Path,
        *,
        operation_id: str | None = None,
    ) -> Operation:
        if self.operation is not None:
            raise InvalidOperationTransition(
                "An operation is already active"
            )

        self.operation = create_operation(
            Path(shuttle_path),
            operation_id=operation_id,
        )

        self.decisions = None
        self.approval_plan = None
        self.import_result = None
        self.certificate = None

        return self.operation

    def require_operation(self) -> Operation:
        if self.operation is None:
            raise InvalidOperationTransition(
                "No operation is active"
            )

        return self.operation

    def validate_snapshot(self) -> bool:
        operation = self.require_operation()

        valid = snapshot_matches_current(
            operation.snapshot
        )

        if not valid:
            self.operation = replace(
                operation,
                state=OperationState.INVALIDATED,
            )

        return valid

    def require_valid_snapshot(self) -> None:
        if not self.validate_snapshot():
            raise OperationInvalidated(
                "The shuttle no longer matches the operation snapshot"
            )

    def attach_decisions(self, decisions: Any) -> None:
        operation = self.require_operation()

        if operation.state not in {
            OperationState.SNAPSHOT_READY,
        }:
            raise InvalidOperationTransition(
                f"Cannot attach decisions while state is "
                f"{operation.state.value}"
            )

        self.require_valid_snapshot()
        self.decisions = decisions

    def attach_approval_plan(self, approval_plan: Any) -> None:
        operation = self.require_operation()

        if self.decisions is None:
            raise InvalidOperationTransition(
                "Decisions must be attached before approval"
            )

        if operation.state is not OperationState.SNAPSHOT_READY:
            raise InvalidOperationTransition(
                f"Cannot attach approval while state is "
                f"{operation.state.value}"
            )

        self.require_valid_snapshot()
        self.approval_plan = approval_plan

    def approve(self) -> None:
        operation = self.require_operation()

        if self.approval_plan is None:
            raise InvalidOperationTransition(
                "An approval plan must exist before approval"
            )

        if operation.state is not OperationState.SNAPSHOT_READY:
            raise InvalidOperationTransition(
                f"Cannot approve while state is "
                f"{operation.state.value}"
            )

        self.require_valid_snapshot()

        self.operation = replace(
            operation,
            state=OperationState.APPROVED,
        )

    def begin_import(self) -> None:
        operation = self.require_operation()

        if operation.state is not OperationState.APPROVED:
            raise InvalidOperationTransition(
                f"Cannot begin import while state is "
                f"{operation.state.value}"
            )

        self.require_valid_snapshot()

        self.operation = replace(
            operation,
            state=OperationState.IMPORTING,
        )

    def complete(
        self,
        *,
        import_result: Any,
        certificate: Any,
    ) -> None:
        operation = self.require_operation()

        if operation.state is not OperationState.IMPORTING:
            raise InvalidOperationTransition(
                f"Cannot complete while state is "
                f"{operation.state.value}"
            )

        self.import_result = import_result
        self.certificate = certificate

        self.operation = replace(
            operation,
            state=OperationState.COMPLETE,
        )

    def clear(self) -> None:
        self.operation = None
        self.decisions = None
        self.approval_plan = None
        self.import_result = None
        self.certificate = None
