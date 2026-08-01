from pathlib import Path
from deckflix_app.config import load_config
from deckflix_app.decision import ApprovalStatus
from deckflix_app.operation import (
    InvalidOperationTransition,
    OperationManager,
    approve_ready_items,
    delete_saved_operation,
    execute_operation,
    load_operation_manager,
    prepare_operation,
    save_operation_manager,
)
from deckflix_app.dashboard import show_dashboard
from deckflix_app.health import library_report, quality_score, size_gb
from deckflix_app.home_screen import show_home_screen
from deckflix_app.import_queue import build_import_queue
from deckflix_app.importer import print_certificate
from deckflix_app.queue_screen import show_queue
from deckflix_app.scanner import scan_videos
from deckflix_app.shuttle import scan_shuttle as shuttle_scan, compare_to_library
from deckflix_app.screens import (
    show_managed_approval_plan,
    show_managed_decision_queue,
    show_operation_dashboard,
    show_operation_history,
    show_parser_diagnostics,
    show_receive_shuttle,
)
from deckflix_app.import_runner import run_import
from deckflix_app.version import APP_NAME, VERSION, CODENAME
from deckflix_app.library_health import show_library_health
from deckflix_app.duplicate_inspector import show_duplicate_inspector
from deckflix_app.repair_queue_screen import show_repair_queue


CONFIG = load_config()

OPERATION_STATE_PATH = (
    CONFIG.report_directory
    / "current-operation.json"
)

try:
    OPERATION_MANAGER = load_operation_manager(
        OPERATION_STATE_PATH
    )
except Exception:
    OPERATION_MANAGER = OperationManager()

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
        operation_manager=OPERATION_MANAGER,
    )



def begin_operation():
    print()
    print("Begin Shuttle Operation")
    print("═══════════════════════")

    if OPERATION_MANAGER.active:
        operation = OPERATION_MANAGER.require_operation()

        print()
        print("An operation is already active.")
        print(f"ID     {operation.id}")
        print(f"State  {operation.state.value}")
        print()
        print("Use Operation Dashboard to review it.")
        return

    print()
    print("Creating immutable shuttle snapshot...")
    print("Building decision queue...")
    print("Building approval plan...")

    try:
        operation = prepare_operation(
            OPERATION_MANAGER,
            shuttle_path=SHUTTLE,
            movie_libraries=CONFIG.movie_libraries,
            tv_libraries=CONFIG.tv_libraries,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print()
        print("Operation could not be created.")
        print(exc)
        return
    except InvalidOperationTransition as exc:
        print()
        print("Operation state error.")
        print(exc)
        return

    print()
    print("Operation Ready")
    print("───────────────")
    print(f"ID                 {operation.id}")
    print(f"State              {operation.state.value}")
    print(
        f"Snapshot files     "
        f"{operation.snapshot.file_count}"
    )
    print(
        f"Decisions          "
        f"{OPERATION_MANAGER.decisions.total}"
    )
    save_operation_manager(
        OPERATION_MANAGER,
        OPERATION_STATE_PATH,
    )

    print()
    print("Nothing has been imported or changed.")


def operation_dashboard():
    show_operation_dashboard(OPERATION_MANAGER)


def clear_operation():
    print()
    print("Clear Current Operation")
    print("═══════════════════════")

    if not OPERATION_MANAGER.active:
        print()
        print("No operation is active.")
        return

    operation = OPERATION_MANAGER.require_operation()

    print()
    print(f"Operation  {operation.id}")
    print(f"State      {operation.state.value}")
    print()

    answer = input(
        "Discard this in-memory operation? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Operation retained.")
        return

    OPERATION_MANAGER.clear()
    delete_saved_operation(OPERATION_STATE_PATH)
    print("Operation cleared.")


def approve_operation():
    print()
    print("Approve Ready Imports")
    print("═════════════════════")

    if not OPERATION_MANAGER.active:
        print()
        print("No operation is active.")
        return

    plan = OPERATION_MANAGER.approval_plan

    if plan is None:
        print()
        print("No approval plan is available.")
        return

    ready = plan.count(ApprovalStatus.READY)

    print()
    print(f"Operation          {OPERATION_MANAGER.operation.id}")
    print(f"Ready imports      {ready}")
    print(f"Needs review       {plan.count(ApprovalStatus.REVIEW)}")
    print(f"Skipped            {plan.count(ApprovalStatus.SKIPPED)}")
    print()
    print("Only NEW media marked READY will be approved.")
    print("Upgrades and review items will not be approved.")

    answer = input(
        "Approve all READY imports? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Approval cancelled.")
        return

    try:
        approved = approve_ready_items(OPERATION_MANAGER)
    except InvalidOperationTransition as exc:
        print()
        print(f"Approval failed: {exc}")
        return

    save_operation_manager(
        OPERATION_MANAGER,
        OPERATION_STATE_PATH,
    )

    print()
    print(f"Approved {approved} import(s).")
    print("No files have been copied.")


def execute_current_operation():
    print()
    print("Execute Operation")
    print("═════════════════")

    if not OPERATION_MANAGER.active:
        print()
        print("No operation is active.")
        return

    if CONFIG.read_only:
        print()
        print("IMPORT BLOCKED")
        print("──────────────")
        print("DeckFlix is currently in SAFE MODE.")
        print("Configuration setting: read_only = true")
        print()
        print("No files have been copied, moved, or deleted.")
        return

    answer = input(
        "Execute all approved imports? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Import cancelled.")
        return

    try:
        certificate = execute_operation(
            OPERATION_MANAGER,
            movie_library=MOVIES,
            tv_library=TV,
            temp_dir=Path("/tmp/deckflix-import"),
            read_only=CONFIG.read_only,
        )
    except Exception as exc:
        print()
        print(f"Import failed: {exc}")
        return

    if certificate is not None:
        print_certificate(certificate)

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
            begin_operation()

        elif choice == "2":
            operation_dashboard()

        elif choice == "3":
            receive_shuttle()

        elif choice == "4":
            show_decision_queue(
                shuttle_path=SHUTTLE,
                movie_libraries=CONFIG.movie_libraries,
                tv_libraries=CONFIG.tv_libraries,
            )

        elif choice == "5":
            show_approval_plan(
                shuttle_path=SHUTTLE,
                movie_libraries=CONFIG.movie_libraries,
                tv_libraries=CONFIG.tv_libraries,
            )

        elif choice == "6":
            import_queue()

        elif choice == "7":
            library_health()

        elif choice == "8":
            duplicate_inspector()

        elif choice == "9":
            show_repair_queue()

        elif choice == "10":
            show_parser_diagnostics(SHUTTLE)

        elif choice == "11":
            ship_mode()

        elif choice == "12":
            show_dashboard(MOVIES, TV, SHUTTLE)

        elif choice == "13":
            clear_operation()

        elif choice == "14":
            print("Securing DeckFlix console.")
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

        print("1. Begin Shuttle Operation")
        print("2. Operation Dashboard")
        print("3. Receive Shuttle Preview")
        print("4. Decision Queue")
        print("5. Decision Approval")
        print("6. Approve Ready Imports")
        print("7. Execute Operation")
        print("8. Operation History")
        print("9. Parser Diagnostics")
        print("10. Library Health")
        print("11. Duplicate Inspector")
        print("12. Repair Queue")
        print("13. Ship Mode")
        print("14. Bridge Dashboard")
        print("15. Clear Current Operation")
        print("16. Exit")
        print()

        choice = input("Select option: ").strip()

        if not choice:
            continue

        if choice == "1":
            begin_operation()

        elif choice == "2":
            operation_dashboard()

        elif choice == "3":
            receive_shuttle()

        elif choice == "4":
            show_managed_decision_queue(OPERATION_MANAGER)

        elif choice == "5":
            show_managed_approval_plan(OPERATION_MANAGER)

        elif choice == "6":
            approve_operation()

        elif choice == "7":
            execute_current_operation()

        elif choice == "8":
            show_operation_history(
                CONFIG.report_directory / "operations"
            )

        elif choice == "9":
            show_parser_diagnostics(SHUTTLE)

        elif choice == "10":
            library_health()

        elif choice == "11":
            duplicate_inspector()

        elif choice == "12":
            show_repair_queue()

        elif choice == "13":
            ship_mode()

        elif choice == "14":
            show_dashboard(MOVIES, TV, SHUTTLE)

        elif choice == "15":
            clear_operation()

        elif choice == "16":
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
