from pathlib import Path

from deckflix_app.app import logo

from deckflix_app.maintenance.upgrades.history import (
    show_upgrade_history,
)


def shuttle_menu():
    while True:
        print()
        print("Shuttle Operation")
        print("─────────────────")
        print("1. Begin Shuttle Operation")
        print("2. Operation Dashboard")
        print("3. Clear Current Operation")
        print("4. Back")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":
            begin_operation()

        elif choice == "2":
            operation_dashboard()

        elif choice == "3":
            clear_operation()

        elif choice == "4":
            break

        else:
            print("Invalid option.")


def repair_menu():
    while True:
        print()
        print("Review & Approve Repairs")
        print("───────────────────────")
        print("1. Review Decisions")
        print("2. Duplicate Inspector")
        print("3. Repair Queue")
        print("4. Upgrade History")
        print("5. Back")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":

            show_managed_decision_queue(
                OPERATION_MANAGER
            )

        elif choice == "2":

            duplicate_inspector()

        elif choice == "3":

            show_repair_queue()

        elif choice == "4":

            show_upgrade_history(
                CONFIG.report_directory
                / "upgrades"
                / "upgrade-history.json"
            )

        elif choice == "5":

            break

        else:
            print("Invalid option.")


def import_menu():
    while True:
        print()
        print("Import Media")
        print("────────────")
        print("1. Approve Ready Imports")
        print("2. Full Import Preflight")
        print("3. Enable Import Mode")
        print("4. Execute Operation")
        print("5. Back")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":

            approve_operation()

        elif choice == "2":

            full_import_preflight()

        elif choice == "3":

            enable_import_mode()

        elif choice == "4":

            execute_current_operation()

        elif choice == "5":

            break

        else:
            print("Invalid option.")


def system_menu():
    while True:
        print()
        print("System Status")
        print("─────────────")
        print("1. Parser Diagnostics")
        print("2. System Verification")
        print("3. Operating Mode")
        print("4. Back")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":

            show_parser_diagnostics(
                SHUTTLE
            )

        elif choice == "2":

            system_verification()

        elif choice == "3":

            changed = show_operating_modes(
                CONFIG
            )

            if changed:
                print()
                print(
                    "Exit and relaunch DeckFlix before "
                    "starting or continuing an operation."
                )

        elif choice == "4":

            break

        else:
            print("Invalid option.")


def main():

    while True:

        logo()

        print(
            "1. Shuttle Operation"
        )

        print(
            "2. Library Health"
        )

        print(
            "3. Review & Approve Repairs"
        )

        print(
            "4. Import Media"
        )

        print(
            "5. Operation History"
        )

        print(
            "6. System Status"
        )

        print(
            "7. Settings"
        )

        print(
            "8. Exit"
        )

        print()

        choice = input(
            "Select option: "
        ).strip()


        if choice == "1":

            shuttle_menu()


        elif choice == "2":

            library_health()


        elif choice == "3":

            repair_menu()


        elif choice == "4":

            import_menu()


        elif choice == "5":

            show_operation_history(
                CONFIG.report_directory
                / "operations"
            )


        elif choice == "6":

            system_menu()


        elif choice == "7":

            print(
                "Settings coming soon."
            )


        elif choice == "8":

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
