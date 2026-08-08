from pathlib import Path

from .plan import (
    CleanupPlan,
    CleanupAction,
    CleanupActionType,
)


def create_empty_directory_plan(
    source: Path,
) -> CleanupPlan:

    plan = CleanupPlan(
        source=source,
    )

    for item in source.rglob("*"):

        if not item.is_dir():
            continue

        try:
            next(item.iterdir())

        except StopIteration:

            plan.actions.append(
                CleanupAction(
                    action=(
                        CleanupActionType
                        .REMOVE_EMPTY_DIRECTORY
                    ),
                    path=item,
                    reason="Empty directory",
                )
            )

    return plan
