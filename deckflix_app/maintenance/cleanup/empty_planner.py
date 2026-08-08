from pathlib import Path

from .plan import (
    CleanupPlan,
    CleanupAction,
    CleanupActionType,
)


PROTECTED_DIRECTORY_SUFFIXES = {
    ".app",
}


def is_inside_protected_directory(
    path: Path,
) -> bool:

    return any(
        parent.suffix.lower()
        in PROTECTED_DIRECTORY_SUFFIXES
        for parent in path.parents
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

        if is_inside_protected_directory(
            item,
        ):
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
