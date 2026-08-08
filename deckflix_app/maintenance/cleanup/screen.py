from pathlib import Path

from .planner import create_cleanup_plan
from .certificate import print_cleanup_certificate
from .execution import execute_cleanup
from .plan import CleanupActionType


def show_cleanup_preview(
    source: Path,
):

    plan = create_cleanup_plan(
        source,
    )

    empty_directories = sum(
        1
        for action in plan.actions
        if action.action
        is CleanupActionType.REMOVE_EMPTY_DIRECTORY
    )

    file_removals = sum(
        1
        for action in plan.actions
        if action.action
        is CleanupActionType.REMOVE_FILE
    )

    print()

    print(
        "DECKFLIX SOURCE CLEANUP"
    )

    print(
        "═══════════════════════"
    )

    print()

    print(
        "Source:"
    )

    print(
        source
    )

    print()

    print(
        "Cleanup Actions"
    )

    print(
        "───────────────"
    )

    print(
        f"Empty directories : {empty_directories}"
    )

    print(
        f"File removals     : {file_removals}"
    )

    print()

    print(
        f"Protected Files   : {plan.protected_files}"
    )

    print(
        f"Review Files      : {plan.review_files}"
    )

    print()

    print(
        "Examples"
    )

    print(
        "────────"
    )

    for action in plan.actions[:10]:

        print()

        print(
            action.action.value
        )

        print(
            action.path
        )

        print(
            action.reason
        )

    print()

    print(
        "[E] Execute Cleanup"
    )

    print(
        "[B] Back"
    )

    print()

    choice = input(
        "Select option: "
    ).strip().lower()


    if choice != "e":
        return


    print()

    print(
        "Cleanup Execution Warning"
    )

    print(
        "════════════════════════"
    )

    print()

    print(
        f"Empty directories : {empty_directories}"
    )

    print(
        f"File removals     : {file_removals}"
    )

    print()

    confirm = input(
        "Type YES to continue: "
    ).strip()


    if confirm != "YES":

        print(
            "Cleanup cancelled."
        )

        return


    journal_path = (
        Path(
            "/data/library1/deckflix-logs/maintenance"
        )
        / "cleanup-journal.json"
    )


    journal = execute_cleanup(
        plan,
        journal_path,
    )


    print_cleanup_certificate(
        journal
    )

    input(
        "\nPress Enter to continue..."
    )
