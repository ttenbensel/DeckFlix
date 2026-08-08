from pathlib import Path

from .scanner import scan_orphans


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

        print()


        choice = input(
            "Select option: "
        ).strip().lower()


        if choice == "b":
            return


        elif choice == "m":

            print()

            print(
                "MIGRATION LEFTOVERS"
            )

            print(
                "──────────────────"
            )

            for item in migration[:20]:
                print()
                print(item.path)


            input(
                "\nPress Enter..."
            )


        elif choice == "r":

            print()

            print(
                "RELEASE JUNK"
            )

            print(
                "────────────"
            )

            for item in release[:20]:
                print()
                print(item.path)


            input(
                "\nPress Enter..."
            )


        elif choice == "o":

            print()

            print(
                "ORPHAN MOVIES"
            )

            print(
                "─────────────"
            )

            for item in orphan[:20]:
                print()
                print(item.path)


            input(
                "\nPress Enter..."
            )
