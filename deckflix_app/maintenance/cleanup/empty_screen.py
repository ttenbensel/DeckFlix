from pathlib import Path

from .empty_planner import (
    create_empty_directory_plan,
)

from .execution import (
    execute_cleanup,
)

from .certificate import (
    print_cleanup_certificate,
)


def show_empty_cleanup(
    source: Path,
):

    plan = create_empty_directory_plan(
        source,
    )

    print()

    print(
        "DECKFLIX EMPTY DIRECTORY CLEANUP"
    )

    print(
        "═══════════════════════════════"
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
        f"Empty folders found: "
        f"{plan.total_actions}"
    )

    print()

    if not plan.actions:

        print(
            "No empty directories found."
        )

        input(
            "\nPress Enter to return..."
        )

        return


    print(
        "Examples"
    )

    print(
        "────────"
    )

    for action in plan.actions[:10]:

        print(
            action.path
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
        "EMPTY DIRECTORY CLEANUP WARNING"
    )

    print(
        "══════════════════════════════"
    )

    print()

    print(
        f"Folders to remove: "
        f"{plan.total_actions}"
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
        / "empty-directory-cleanup-journal.json"
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
