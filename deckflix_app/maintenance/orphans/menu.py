from pathlib import Path

from .scanner import scan_orphans
from .detail import show_orphan_detail
from .health_report import show_health_report
from .plan_screen import show_cleanup_plan
from .planner import create_orphan_cleanup_plan
from .quality_screen import show_quality_review


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

        if not items:

            print(
                "No items found"
            )

        else:

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


        plan = create_orphan_cleanup_plan(
            results
        )


        print()

        show_health_report(
            source,
            destination,
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
            "[P] View cleanup plan"
        )

        print(
            "[Q] View quality review"
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


        elif choice == "p":

            show_cleanup_plan(
                plan
            )


        elif choice == "q":

            show_quality_review(
                source,
                destination,
            )
