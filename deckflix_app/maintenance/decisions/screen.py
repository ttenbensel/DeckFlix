from pathlib import Path

from .models import (
    Decision,
    DecisionType,
)

from .journal import (
    DecisionJournal,
)


def show_decision_screen(
    item,
    journal_path: Path,
):

    journal = DecisionJournal(
        journal_path
    )


    while True:

        print()

        print(
            "DECKFLIX DECISION REQUIRED"
        )

        print(
            "══════════════════════════"
        )

        print()

        print(
            item.classification.value
        )

        print()

        print(
            "TITLE"
        )

        print(
            "─────"
        )

        print(
            item.source.title
        )

        if item.source.year:

            print(
                f"Year: {item.source.year}"
            )


        print()

        print(
            "REASON"
        )

        print(
            "──────"
        )

        print(
            item.reason
        )


        print()

        print(
            "[U] Upgrade"
        )

        print(
            "[K] Keep current"
        )

        print(
            "[I] Ignore"
        )

        print(
            "[B] Back"
        )


        choice = input(
            "Decision: "
        ).strip().lower()


        if choice == "b":

            return


        if choice == "u":

            decision = DecisionType.UPGRADE


        elif choice == "k":

            decision = DecisionType.KEEP


        elif choice == "i":

            decision = DecisionType.IGNORE


        else:

            continue


        journal.add(
            Decision(
                title=item.source.title,
                decision=decision,
                classification=(
                    item.classification.value
                ),
                reason=item.reason,
                source_path=item.source.path,
                destination_path=(
                    item.destination.path
                ),
            )
        )

        journal.save()


        print()

        print(
            "Decision saved"
        )

        input(
            "Press Enter to continue..."
        )

        return
