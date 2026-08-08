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

    directories = sorted(
        (
            item
            for item in source.rglob("*")
            if item.is_dir()
        ),
        key=lambda p: len(p.parts),
        reverse=True,
    )

    for item in directories:

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
