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
    run_import_preflight,
    prepare_operation,
    save_operation_manager,
)
from deckflix_app.health import library_report, quality_score, size_gb
from deckflix_app.home_screen import show_home_screen
from deckflix_app.importer import print_certificate
from deckflix_app.screens import (
    show_operating_modes,
    show_system_verification,
    TerminalImportMonitor,
    show_managed_decision_queue,
    show_operation_dashboard,
    show_import_preflight,
    show_operation_history,
    show_parser_diagnostics,
)
from deckflix_app.version import APP_NAME, VERSION, CODENAME
from deckflix_app.system_verification import run_system_verification
from deckflix_app.library_health import show_library_health
from deckflix_app.duplicate_inspector import show_duplicate_inspector
from deckflix_app.repair_queue_screen import show_repair_queue
from deckflix_app.maintenance_ui import (
    system_verification,
    library_health,
    repair_preview,
    duplicate_inspector,
)
from deckflix_app.operations_ui import (
    begin_operation,
    operation_dashboard,
    clear_operation,
    approve_operation,
    full_import_preflight,
    enable_import_mode,
    execute_current_operation,
)


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



def main():
    while True:
        logo()

        print("1. Begin Shuttle Operation")
        print("2. Operation Dashboard")
        print("3. Review Decisions")
        print("4. Approve Ready Imports")
        print("5. Full Import Preflight")
        print("6. Enable Import Mode")
        print("7. Execute Operation")
        print("8. Operation History")
        print("9. Library Health")
        print("10. Duplicate Inspector")
        print("11. Repair Queue")
        print("12. Parser Diagnostics")
        print("13. System Verification")
        print("14. Operating Mode")
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
            show_managed_decision_queue(
                OPERATION_MANAGER
            )

        elif choice == "4":
            approve_operation()

        elif choice == "5":
            full_import_preflight(
                operation_manager=OPERATION_MANAGER,
                movies=MOVIES,
                tv=TV,
                config=CONFIG,
            )

        elif choice == "6":
            enable_import_mode(
                operation_manager=OPERATION_MANAGER,
                operation_state_path=OPERATION_STATE_PATH,
            )

        elif choice == "7":
            execute_current_operation()

        elif choice == "8":
            show_operation_history(
                CONFIG.report_directory
                / "operations"
            )

        elif choice == "9":
            library_health()

        elif choice == "10":
            duplicate_inspector()

        elif choice == "11":
            show_repair_queue()

        elif choice == "12":
            show_parser_diagnostics(
                SHUTTLE
            )

        elif choice == "13":
            system_verification()

        elif choice == "14":
            changed = show_operating_modes(CONFIG)

            if changed:
                print()
                print(
                    "Exit and relaunch DeckFlix before "
                    "starting or continuing an operation."
                )

        elif choice == "15":
            clear_operation()

        elif choice == "16":
            print("Securing DeckFlix console.")
            break

        else:
            print("Invalid option.")

        input(
            "\nPress Enter to return to menu..."
        )


