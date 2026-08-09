from pathlib import Path

from .journal import DecisionJournal


def show_decision_history(
    path: Path,
):

    journal = DecisionJournal.load(
        path
    )


    print()

    print(
        "DECKFLIX DECISION HISTORY"
    )

    print(
        "════════════════════════"
    )


    print()


    if not journal.entries:

        print(
            "No decisions recorded"
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
                f"   Classification: "
                f"{entry.classification}"
            )

            print(
                f"   Decision: "
                f"{entry.decision}"
            )

            print(
                f"   Reason: "
                f"{entry.reason}"
            )

            print(
                f"   Date: "
                f"{entry.created_at}"
            )

            print()



    input(
        "Press Enter to continue..."
    )
