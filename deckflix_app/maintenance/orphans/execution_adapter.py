from deckflix_app.maintenance.cleanup.plan import (
    CleanupPlan,
    CleanupAction,
    CleanupActionType,
)

from .planner import (
    OrphanCleanupPlan,
)


def convert_orphan_plan(
    plan: OrphanCleanupPlan,
) -> CleanupPlan:

    cleanup_plan = CleanupPlan(
        source=plan.source
    )

    for item in plan.actions:

        if item.classification.value == "MIGRATION_LEFTOVER":

            cleanup_plan.actions.append(
                CleanupAction(
                    action=(
                        CleanupActionType.REMOVE_DIRECTORY_TREE
                    ),
                    path=item.path,
                    reason=(
                        "Migration leftover - "
                        "media verified in destination"
                    ),
                )
            )


        elif item.classification.value == "RELEASE_JUNK":

            cleanup_plan.actions.append(
                CleanupAction(
                    action=(
                        CleanupActionType.REMOVE_DIRECTORY_TREE
                    ),
                    path=item.path,
                    reason=(
                        "Release junk - "
                        "no playable media found"
                    ),
                )
            )


    return cleanup_plan
