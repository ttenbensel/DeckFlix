from pathlib import Path

from .planner import (
    OrphanCleanupPlan,
)


def show_cleanup_plan(
    plan: OrphanCleanupPlan,
):

    migration = 0
    release = 0

    for item in plan.actions:

        if item.classification.value == "MIGRATION_LEFTOVER":
            migration += 1

        elif item.classification.value == "RELEASE_JUNK":
            release += 1


    print()

    print(
        "DECKFLIX CLEANUP PLAN"
    )

    print(
        "═════════════════════"
    )

    print()

    print(
        "Source:"
    )

    print(
        plan.source
    )

    print()

    print(
        f"Migration leftovers : {migration}"
    )

    print(
        f"Release junk        : {release}"
    )

    print()

    print(
        "Excluded"
    )

    print(
        "────────"
    )

    print(
        "Orphan movies       : Manual review only"
    )

    print()

    print(
        "Actions:"
    )

    print(
        plan.total_actions
    )

    print()

    print(
        "Examples"
    )

    print(
        "────────"
    )

    for item in plan.actions[:10]:

        print()

        print(
            item.classification.value
        )

        print(
            item.path
        )

    print()

    print(
        "[E] Execute Cleanup"
    )

    print(
        "[B] Back"
    )

    return input(
        "Select option: "
    ).strip().lower()
