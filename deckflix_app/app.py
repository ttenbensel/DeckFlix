from deckflix_app.config import load_config
from deckflix_app.dashboard import show_dashboard
from deckflix_app.health import library_report, quality_score, size_gb
from deckflix_app.home_screen import show_home_screen
from deckflix_app.import_queue import build_import_queue
from deckflix_app.queue_screen import show_queue
from deckflix_app.scanner import scan_videos
from deckflix_app.shuttle import scan_shuttle as shuttle_scan, compare_to_library
from deckflix_app.screens import (
    show_parser_diagnostics,
    show_receive_shuttle,
)
from deckflix_app.import_runner import run_import
from deckflix_app.version import APP_NAME, VERSION, CODENAME
from deckflix_app.library_health import show_library_health
from deckflix_app.duplicate_inspector import show_duplicate_inspector
from deckflix_app.repair_queue_screen import show_repair_queue


CONFIG = load_config()

MOVIES = CONFIG.movie_libraries[0]
TV = CONFIG.tv_libraries[0]
SHUTTLE = CONFIG.shuttle
QUARANTINE = CONFIG.paths.quarantine


def logo():
    show_home_screen(
        app_name=APP_NAME,
        version=VERSION,
        codename=CODENAME,
        config=CONFIG,
    )


def build_current_queue():
    shuttle = shuttle_scan(SHUTTLE)
    library_movies = scan_videos(MOVIES)
    comparison = compare_to_library(shuttle["media"], library_movies)
    return build_import_queue(comparison, library_movies)


def receive_shuttle():
    show_receive_shuttle(
        shuttle_path=SHUTTLE,
        movie_library_path=MOVIES,
    )


def import_queue():
    queue = build_current_queue()
    show_queue(queue)

    while True:
        print()
        print("Queue Options")
        print("─────────────")
        print("1. Run approved imports")
        print("2. Return to main menu")
        print()

        choice = input("Select option: ").strip()

        if not choice:
            continue

        if choice == "1":
            success = run_import(
                queue,
                MOVIES,
                TV,
            )

            if success:
                input("\nPress Enter after verifying the copy...")

            break

        elif choice == "2":
            break

        else:
            print("Invalid option.")


def library_health():
    show_library_health(
        MOVIES,
        TV,
    )

    input("\nPress Enter to return to the main menu...")


def repair_preview():
    report = library_report(MOVIES, TV)

    while True:
        print()
        print("Repair Preview")
        print("──────────────")
        print("Dry-run only. Nothing will be moved, renamed, or deleted.")
        print()
        print(f"1. Review sample/junk files       {len(report['junk'])}")
        print(f"2. Review nested movie warnings   {len(report['nested'])}")
        print(f"3. Review duplicate groups        {len(report['duplicates'])}")
        print("4. Quarantine information")
        print("5. Back")
        print()

        choice = input("Select repair option: ").strip()

        if choice == "1":
            print()
            print("Sample/Junk Files")
            print("─────────────────")
            if report["junk"]:
                for file in report["junk"]:
                    print(f"[WOULD QUARANTINE] {file}")
            else:
                print("None found")
            input("\nPress Enter to continue...")

        elif choice == "2":
            print()
            print("Nested Movie Warnings")
            print("─────────────────────")
            if report["nested"]:
                for file in report["nested"][:50]:
                    print(f"[WOULD REVIEW MOVE] {file}")
                if len(report["nested"]) > 50:
                    print(f"...and {len(report['nested']) - 50} more")
            else:
                print("None found")
            input("\nPress Enter to continue...")

        elif choice == "3":
            print()
            print("Duplicate Review")
            print("────────────────")
            shown = 0
            for title, files in sorted(report["duplicates"].items()):
                ranked = sorted(files, key=quality_score, reverse=True)
                keep = ranked[0]

                print()
                print(title.title())
                print(f"[KEEP]   score {quality_score(keep):>3} {size_gb(keep):>5.1f} GB {keep}")

                for file in ranked[1:]:
                    print(f"[REVIEW] score {quality_score(file):>3} {size_gb(file):>5.1f} GB {file}")

                shown += 1
                if shown >= 20:
                    break

            input("\nPress Enter to continue...")

        elif choice == "4":
            print()
            print("Quarantine")
            print("──────────")
            print("Future repair actions will move files here first:")
            print(QUARANTINE)
            print()
            print("DeckFlix rule:")
            print("Never delete first. Quarantine, verify, then remove later.")
            input("\nPress Enter to continue...")

        elif choice == "5":
            break

        else:
            print("Invalid option.")


def ship_mode():
    print()
    print("Ship Mode")
    print("─────────")
    print("Current Mode      ⚓ Harbour")
    print("Low Impact        Enabled")
    print("Internet Tasks    Allowed")
    print("Background Work   Normal")
    print()
    print("Sea Mode controls coming next.")


def main():
    while True:
        logo()

        print("1. Bridge Dashboard")
        print("2. Receive Shuttle")
        print("3. Import Queue")
        print("4. Library Health")
        print("5. Duplicate Inspector")
        print("6. Repair Queue")
        print("7. Ship Mode")
        print("8. Parser Diagnostics")
        print("9. Exit")
        print()

        choice = input("Select option: ").strip()

        if not choice:
            continue

        if choice == "1":
            show_dashboard(MOVIES, TV, SHUTTLE)

        elif choice == "2":
            receive_shuttle()

        elif choice == "3":
            import_queue()

        elif choice == "4":
            library_health()

        elif choice == "5":
            duplicate_inspector()

        elif choice == "6":
            show_repair_queue()

        elif choice == "7":
            ship_mode()

        elif choice == "8":
            show_parser_diagnostics(SHUTTLE)

        elif choice == "9":
            print("Securing DeckFlix console.")
            break

        else:
            print("Invalid option.")

        input("\nPress Enter to return to menu...")
        

def duplicate_inspector():
    show_duplicate_inspector(
        MOVIES,
        TV,
    )

    input("\nPress Enter to return to the main menu...")
