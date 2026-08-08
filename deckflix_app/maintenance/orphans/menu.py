from pathlib import Path

from .scanner import scan_orphans
from .detail import show_orphan_detail


def show_list(
    title,
    items,
):

    while True:

        print()

        print(title)

        print(
            "─────────────"
        )

        for index, item in enumerate(
            items,
            start=1,
        ):
            print(
                f"{index}. {item.path.name}"
            )

        print()

        print(
            "[B] Back"
        )

        choice = input(
            "Select item: "
        ).strip().lower()


        if choice == "b":
            return


        if choice.isdigit():

            number = int(choice)

            if (
                number >= 1
                and number <= len(items)
            ):
                show_orphan_detail(
                    items[number - 1]
                )


def show_orphan_menu(
    source: Path,
    destination: Path,
):

    while True:

        results = scan_orphans(
            source,
            destination,
        )


        migration = [
            item
            for item in results
            if item.classification.value
            == "MIGRATION_LEFTOVER"
        ]

        release = [
            item
            for item in results
            if item.classification.value
            == "RELEASE_JUNK"
        ]

        orphan = [
            item
            for item in results
            if item.classification.value
            == "ORPHAN_MOVIE"
        ]


        print()

        print(
            "DECKFLIX MEDIA HEALTH"
        )

        print(
            "═════════════════════"
        )

        print()

        print(
            f"Migration leftovers : {len(migration)}"
        )

        print(
            f"Release junk        : {len(release)}"
        )

        print(
            f"Orphan movies       : {len(orphan)}"
        )

        print()

        print(
            "[M] View migration leftovers"
        )

        print(
            "[R] View release junk"
        )

        print(
            "[O] View orphan movies"
        )

        print(
            "[B] Back"
        )


        choice = input(
            "Select option: "
        ).strip().lower()


        if choice == "b":
            return

        elif choice == "m":

            show_list(
                "MIGRATION LEFTOVERS",
                migration,
            )

        elif choice == "r":

            show_list(
                "RELEASE JUNK",
                release,
            )

        elif choice == "o":

            show_list(
                "ORPHAN MOVIES",
                orphan,
            )
