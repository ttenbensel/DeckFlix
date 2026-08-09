from pathlib import Path

from .journal import UpgradeJournal


def show_upgrade_history(
    path: Path,
):

    journal = UpgradeJournal.load(
        path
    )


    print()

    print(
        "DECKFLIX UPGRADE HISTORY"
    )

    print(
        "═══════════════════════"
    )

    print()


    if not journal.entries:

        print(
            "No upgrades recorded"
        )


    else:

        for index, entry in enumerate(
            journal.entries,
            start=1,
        ):

            print(
                f"{index}. {entry.title}"
            )

            print(
                f"   Type: "
                f"{entry.upgrade_type}"
            )

            print(
                f"   Status: "
                f"{entry.status}"
            )

            print(
                f"   Reason: "
                f"{entry.reason}"
            )

            print(
                f"   Source:"
            )

            print(
                f"   {entry.source_path}"
            )

            print(
                f"   Destination:"
            )

            print(
                f"   {entry.destination_path}"
            )

            print(
                f"   Date:"
            )

            print(
                f"   {entry.created_at}"
            )

            print()



    input(
        "Press Enter to continue..."
    )
