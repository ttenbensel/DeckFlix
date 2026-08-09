from pathlib import Path

from .journal import UpgradeJournal
from .models import (
    UpgradeCandidate,
    UpgradeStatus,
)


def show_upgrade_review(
    upgrade: UpgradeCandidate,
    journal_path: Path,
):

    print()

    print(
        "DECKFLIX UPGRADE REVIEW"
    )

    print(
        "═══════════════════════"
    )

    print()

    print(
        "MOVIE"
    )

    print(
        "─────"
    )

    print(
        upgrade.title
    )

    print()

    print(
        "CURRENT FILE"
    )

    print(
        "────────────"
    )

    print(
        upgrade.destination_path
    )

    print()

    print(
        "UPGRADE FILE"
    )

    print(
        "────────────"
    )

    print(
        upgrade.source_path
    )

    print()

    print(
        "REASON"
    )

    print(
        "──────"
    )

    print(
        upgrade.reason
    )

    print()

    print(
        "STATUS"
    )

    print(
        upgrade.status.value
    )

    print()

    print(
        "[A] Approve upgrade"
    )

    print(
        "[B] Back"
    )


    choice = input(
        "Select option: "
    ).strip().lower()


    if choice == "a":

        upgrade.status = (
            UpgradeStatus.APPROVED
        )


        journal = UpgradeJournal.load(
            journal_path
        )

        journal.add(
            upgrade
        )

        journal.save()


        print()

        print(
            "Upgrade approved"
        )

        input(
            "Press Enter to continue..."
        )
