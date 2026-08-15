from pathlib import Path

from deckflix_app.health import (
    library_report,
    quality_score,
    size_gb,
)
from deckflix_app.library_health import show_library_health
from deckflix_app.system_verification import run_system_verification
from deckflix_app.duplicate_inspector import show_duplicate_inspector
from deckflix_app.maintenance.plans_screen import (
    show_maintenance_plans,
)

def system_verification(
    *,
    config,
    operation_manager,
):
    print()
    print("Running DeckFlix system verification...")

    result = run_system_verification(
        config=config,
        operation_manager=operation_manager,
        temp_directory=Path(
            str(config.import_staging_directory)
        ),
    )

    return result


def library_health(
    movies,
    tv,
):
    show_library_health(
        movies,
        tv,
    )


def repair_preview(
    movies,
    tv,
    quarantine,
):
    report = library_report(
        movies,
        tv,
    )

    while True:
        print()
        print("Repair Preview")
        print("──────────────")
        print(
            "Dry-run only. Nothing will be moved, "
            "renamed, or deleted."
        )
        print()

        print(
            f"1. Review sample/junk files       "
            f"{len(report['junk'])}"
        )
        print(
            f"2. Review nested movie warnings   "
            f"{len(report['nested'])}"
        )
        print(
            f"3. Review duplicate groups        "
            f"{len(report['duplicates'])}"
        )
        print("4. Quarantine information")
        print("5. Back")
        print()

        choice = input(
            "Select repair option: "
        ).strip()

        if choice == "1":
            print()
            print("Sample/Junk Files")
            print("─────────────────")

            if report["junk"]:
                for file in report["junk"]:
                    print(
                        f"[WOULD QUARANTINE] {file}"
                    )
            else:
                print("None found")

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "2":
            print()
            print("Nested Movie Warnings")
            print("─────────────────────")

            if report["nested"]:
                for file in report["nested"][:50]:
                    print(
                        f"[WOULD REVIEW MOVE] {file}"
                    )

                if len(report["nested"]) > 50:
                    print(
                        f"...and "
                        f"{len(report['nested']) - 50} more"
                    )
            else:
                print("None found")

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "3":
            print()
            print("Duplicate Review")
            print("────────────────")

            shown = 0

            for title, files in sorted(
                report["duplicates"].items()
            ):
                ranked = sorted(
                    files,
                    key=quality_score,
                    reverse=True,
                )

                keep = ranked[0]

                print()
                print(title.title())

                print(
                    f"[KEEP]   score "
                    f"{quality_score(keep):>3} "
                    f"{size_gb(keep):>5.1f} GB "
                    f"{keep}"
                )

                for file in ranked[1:]:
                    print(
                        f"[REVIEW] score "
                        f"{quality_score(file):>3} "
                        f"{size_gb(file):>5.1f} GB "
                        f"{file}"
                    )

                shown += 1

                if shown >= 20:
                    break

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "4":
            print()
            print("Quarantine")
            print("──────────")
            print(
                "Future repair actions will move files here first:"
            )
            print(quarantine)
            print()
            print("DeckFlix rule:")
            print(
                "Never delete first. "
                "Quarantine, verify, then remove later."
            )

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "5":
            break

        else:
            print("Invalid option.")


def duplicate_inspector(
    movies,
    tv,
):
    show_duplicate_inspector(
        movies,
        tv,
    )

def maintenance_plans(
    directory,
):
    show_maintenance_plans(
        directory,
    )
