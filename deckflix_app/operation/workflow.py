from pathlib import Path

from deckflix_app.decision import (
    build_approval_plan,
    build_decision_queue_from_paths,
)

from .manager import OperationManager
from .models import Operation


def prepare_operation(
    manager: OperationManager,
    *,
    shuttle_path: Path,
    movie_libraries: list[Path],
    tv_libraries: list[Path],
    operation_id: str | None = None,
) -> Operation:
    """
    Create one operation and attach its decisions and approval plan.

    The shuttle snapshot is created first. The manager verifies that
    snapshot again before attaching each downstream stage.
    """
    operation = manager.begin(
        Path(shuttle_path),
        operation_id=operation_id,
    )

    decisions = build_decision_queue_from_paths(
        shuttle_path=operation.snapshot.shuttle_path,
        movie_libraries=[
            Path(path)
            for path in movie_libraries
        ],
        tv_libraries=[
            Path(path)
            for path in tv_libraries
        ],
    )

    manager.attach_decisions(decisions)

    approval_plan = build_approval_plan(decisions)
    manager.attach_approval_plan(approval_plan)

    return manager.require_operation()
