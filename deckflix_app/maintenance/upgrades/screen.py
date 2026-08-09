from pathlib import Path

from .journal import UpgradeJournal
from .models import (
    UpgradeCandidate,
    UpgradeStatus,
)

from .execution import execute_upgrade


def show_upgrade_review(
    upgrade: UpgradeCandidate,
    journal_path: Path,
):

    while True:

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


        if upgrade.status == UpgradeStatus.PENDING:

            print(
                "[A] Approve upgrade"
            )


        if upgrade.status == UpgradeStatus.APPROVED:

            print(
                "[X] Execute upgrade"
            )


        if upgrade.status == UpgradeStatus.EXECUTED:

            print(
                "Upgrade complete"
            )


        print()

        print(
            "[B] Back"
        )


        choice = input(
            "Select option: "
        ).strip().lower()


        if choice == "b":

            return


        elif (
            choice == "a"
            and upgrade.status
            == UpgradeStatus.PENDING
        ):

            upgrade.status = (
                UpgradeStatus.APPROVED
            )


            journal = UpgradeJournal.load(
                journal_path
            )

            journal.update(
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


        elif (
            choice == "x"
            and upgrade.status
            == UpgradeStatus.APPROVED
        ):

            execute_upgrade(
                upgrade,
                journal_path,
            )


            print()

            print(
                "Upgrade executed"
            )


            input(
                "Press Enter to continue..."
            )
