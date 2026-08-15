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

from deckflix_app.health import (
    library_report,
    quality_score,
    size_gb,
)

from deckflix_app.home_screen import show_home_screen
from deckflix_app.importer import print_certificate

from deckflix_app.screens import (
    show_operating_modes,
    show_system_verification,
    show_ship_status,
    TerminalImportMonitor,
    show_managed_decision_queue,
    show_operation_dashboard,
    show_import_preflight,
    show_operation_history,
    show_parser_diagnostics,
)

from deckflix_app.version import (
    APP_NAME,
    VERSION,
    CODENAME,
)

from deckflix_app.system_verification import (
    run_system_verification,
)

from deckflix_app.library_health import (
    show_library_health,
    _build_repair_plan,
    _show_repair_operation,
)

from deckflix_app.library import (
    audit_libraries,
    current_deckflix_library_roots,
)

from deckflix_app.duplicate_inspector import (
    show_duplicate_inspector,
)

from deckflix_app.repair_queue_screen import (
    show_repair_queue,
)

from deckflix_app.maintenance.screen import (
    show_repair_preview,
)

from deckflix_app.maintenance_ui import (
    system_verification,
    library_health,
    repair_preview,
    duplicate_inspector,
    maintenance_plans,
)

from deckflix_app.operations_ui import (
    begin_operation,
    verify_existing_library_copies,
    preserve_review_hold,
    final_snapshot_safety_validation,
    empty_and_eject_preflight,
    operation_dashboard,
    clear_operation,
    approve_operation,
    full_import_preflight,
    enable_import_mode,
    execute_current_operation,
    handle_shuttle_operation_choice,
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

        print("1. Shuttle Operation")
        print("2. Library Health")
        print("3. Review & Approve Repairs")
        print("4. Import Media")
        print("5. Operation History")
        print("6. System Status")
        print("7. Exit")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":
            while True:
                print()
                print("Shuttle Operation")
                print("─────────────────")
                print("1. Begin Shuttle Operation")
                print("2. Verify Existing Library Copies")
                print("3. Preserve Unresolved in Review Hold")
                print("4. Final Safety Validation")
                print("5. Approve Ready Imports")
                print("6. Shuttle Release")
                print("7. Operation Dashboard")
                print("8. Clear Current Operation")
                print("9. Back")
                print()

                sub = input(
                    "Select option: "
                ).strip()

                if sub == "5":
                    approve_operation(
                        operation_manager=OPERATION_MANAGER,
                        operation_state_path=OPERATION_STATE_PATH,
                    )
                    continue

                routed_sub = {
                    "1": "1",
                    "2": "2",
                    "3": "3",
                    "4": "4",
                    "6": "5",
                    "7": "6",
                    "8": "7",
                    "9": "8",
                }.get(sub)

                if routed_sub is None:
                    print("Invalid option.")
                    continue

                stay_in_menu = (
                    handle_shuttle_operation_choice(
                        routed_sub,
                        operation_manager=OPERATION_MANAGER,
                        shuttle=SHUTTLE,
                        config=CONFIG,
                        operation_state_path=OPERATION_STATE_PATH,
                    )
                )

                if not stay_in_menu:
                    break

        elif choice == "2":
            library_health(
                MOVIES,
                TV,
            )

        elif choice == "3":
            while True:
                print()
                print("Review & Approve Repairs")
                print("───────────────────────")
                print("1. Review Decisions")
                print("2. Misplaced TV Content")
                print("3. Duplicate Inspector")
                print("4. Repair Queue")
                print("5. Repair Operation")
                print("6. Maintenance Plans")
                print("7. Back")
                print()

                sub = input(
                    "Select option: "
                ).strip()

                if sub == "1":
                    show_managed_decision_queue(
                        OPERATION_MANAGER
                    )

                elif sub == "2":
                    show_repair_preview(
                        MOVIES,
                        TV,
                    )

                elif sub == "3":
                    duplicate_inspector(
                        MOVIES,
                        TV,
                    )

                elif sub == "4":
                    show_repair_queue()

                elif sub == "5":
                    audit = audit_libraries(
                        current_deckflix_library_roots()
                    )

                    plan = _build_repair_plan(
                        audit
                    )

                    _show_repair_operation(
                        plan
                    )

                elif sub == "6":
                    maintenance_plans(
                        CONFIG.report_directory
                        / "maintenance"
                    )

                elif sub == "7":
                    break

                else:
                    print("Invalid option.")

        elif choice == "4":
            while True:
                print()
                print("Import Media")
                print("────────────")
                print("1. Full Import Preflight")
                print("2. Enable Import Mode")
                print("3. Execute Operation")
                print("4. Back")
                print()

                sub = input(
                    "Select option: "
                ).strip()

                if sub == "1":
                    full_import_preflight(
                        operation_manager=OPERATION_MANAGER,
                        movies=MOVIES,
                        tv=TV,
                        config=CONFIG,
                    )

                elif sub == "2":
                    enable_import_mode(
                        operation_manager=OPERATION_MANAGER,
                        operation_state_path=OPERATION_STATE_PATH,
                        movies=MOVIES,
                        tv=TV,
                        config=CONFIG,
                    )

                elif sub == "3":
                    execute_current_operation(
                        operation_manager=OPERATION_MANAGER,
                        movies=MOVIES,
                        tv=TV,
                        config=CONFIG,
                        operation_state_path=OPERATION_STATE_PATH,
                    )

                elif sub == "4":
                    break

                else:
                    print("Invalid option.")

        elif choice == "5":
            show_operation_history(
                CONFIG.report_directory
                / "operations"
            )

        elif choice == "6":
            while True:
                print()
                print("System Status")
                print("─────────────")
                print("1. Parser Diagnostics")
                print("2. System Verification")
                print("3. Operating Mode")
                print("4. Ship Status Dashboard")
                print("5. Back")
                print()

                sub = input(
                    "Select option: "
                ).strip()

                if sub == "1":
                    show_parser_diagnostics(
                        SHUTTLE
                    )

                elif sub == "2":
                    system_verification(
                        config=CONFIG,
                        operation_manager=OPERATION_MANAGER,
                    )

                elif sub == "3":
                    changed = show_operating_modes(
                        CONFIG
                    )

                    if changed:
                        print()
                        print(
                            "Exit and relaunch DeckFlix before "
                            "starting or continuing an operation."
                        )

                elif sub == "4":
                    show_ship_status(
                        config=CONFIG,
                        operation_manager=OPERATION_MANAGER,
                    )

                elif sub == "5":
                    break

                else:
                    print("Invalid option.")

        elif choice == "7":
            print(
                "Securing DeckFlix console."
            )
            break

        else:
            print(
                "Invalid option."
            )

        input(
            "\nPress Enter to return to menu..."
        )


if __name__ == "__main__":
    main()
