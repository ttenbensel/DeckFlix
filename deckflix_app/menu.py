from deckflix_app.app import logo

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
            full_import_preflight()

        elif choice == "6":
            enable_import_mode()

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
