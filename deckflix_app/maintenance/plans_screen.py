from pathlib import Path

from .manager import MaintenanceManager
from .plan import MaintenanceState
from .preflight import run_preflight
from .executor import execute_dry_run
from .execution import execute_plan
from .certificate import print_maintenance_certificate

def show_maintenance_plans(
    directory: Path,
):
    manager = MaintenanceManager(
        directory,
    )

    while True:
        plans = manager.list_plans()

        print()
        print("Maintenance Plans")
        print("═════════════════")
        print()

        if not plans:
            print("No maintenance plans found.")
            input(
                "\nPress Enter to return..."
            )
            return

        for index, plan_path in enumerate(
            plans,
            start=1,
        ):
            plan = manager.load(
                plan_path,
            )

            print(
                f"{index}. {plan.id}"
            )
            print(
                f"   Actions : "
                f"{plan.total_actions}"
            )
            print(
                f"   State   : "
                f"{plan.state.value}"
            )
            print()

        print("[B] Back")
        print()

        choice = input(
            "Select plan: "
        ).strip().lower()

        if choice == "b":
            return

        if choice.isdigit():
            index = int(choice) - 1

            if 0 <= index < len(plans):
                show_plan_details(
                    manager,
                    plans[index],
                )


def show_plan_details(
    manager,
    plan_path: Path,
):
    plan = manager.load(
        plan_path,
    )

    if plan is None:
        return

    while True:
        print()
        print("Maintenance Plan")
        print("════════════════")
        print()
        print(f"ID      : {plan.id}")
        print(f"Actions : {plan.total_actions}")
        print(f"State   : {plan.state.value}")
        print()

        print("Examples")
        print("────────")

        for action in plan.actions[:10]:
            print()
            print(action.source.name)
            print("FROM:")
            print(action.source.parent)
            print("TO:")
            print(action.destination)

        print()

        if plan.state is MaintenanceState.CREATED:
            print("[A] Approve Plan")

        if plan.state is MaintenanceState.APPROVED:
            print("[P] Run Preflight")
            print("[D] Dry Run Execution")
            print("[E] Execute Repair")

        print("[B] Back")
        print()

        choice = input(
            "Select option: "
        ).strip().lower()

        if choice == "b":
            return

        if (
            choice == "a"
            and plan.state is MaintenanceState.CREATED
        ):
            plan = manager.approve(
                plan,
            )

            print()
            print("Maintenance Plan Approved")
            print("═══════════════════════")
            print()
            print(
                "No files have been moved."
            )

            input(
                "\nPress Enter to continue..."
            )

        elif (
            choice == "p"
            and plan.state is MaintenanceState.APPROVED
        ):
            result = run_preflight(
                plan,
            )

            print()
            print("Maintenance Preflight")
            print("════════════════════")
            print()
            print(
                f"Actions            : "
                f"{result.total_actions}"
            )
            print(
                f"Missing Sources    : "
                f"{result.missing_sources}"
            )
            print(
                f"Destination Issues : "
                f"{result.destination_conflicts}"
            )
            print(
                f"Estimated Bytes    : "
                f"{result.estimated_bytes:,}"
            )
            print()

            if result.safe:
                print(
                    "Result: SAFE TO EXECUTE"
                )
            else:
                print(
                    "Result: REVIEW REQUIRED"
                )

            input(
                "\nPress Enter to continue..."
            )

        elif (
            choice == "d"
            and plan.state is MaintenanceState.APPROVED
        ):
            result = execute_dry_run(
                plan,
            )

            print()
            print("Maintenance Dry Run")
            print("═══════════════════")
            print()
            print(
                f"Actions  : "
                f"{result.total}"
            )
            print(
                f"Reviewed : "
                f"{result.reviewed}"
            )
            print(
                f"Failed   : "
                f"{result.failed}"
            )
            print()

            if result.successful:
                print(
                    "Result: SUCCESS"
                )
            else:
                print(
                    "Result: REVIEW REQUIRED"
                )

            print()
            print(
                "No files have been changed."
            )

            input(
                "\nPress Enter to continue..."
            )

        elif (
            choice == "e"
            and plan.state is MaintenanceState.APPROVED
        ):
            print()
            print("Maintenance Execution Warning")
            print("═══════════════════════════")
            print()
            print(
                f"Plan    : {plan.id}"
            )
            print(
                f"Actions : {plan.total_actions}"
            )
            print()
            print(
                "Mode:"
            )
            print(
                "COPY → VERIFY → REMOVE"
            )
            print()

            confirm = input(
                "Type YES to continue: "
            ).strip()

            if confirm != "YES":
                print(
                    "Execution cancelled."
                )

                input(
                    "\nPress Enter to continue..."
                )

                continue

            journal = execute_plan(
                plan,
                Path(
                    "/data/library1/deckflix-logs/maintenance"
                )
                / f"{plan.id}-journal.json",
            )

            verified = sum(
                1
                for entry in journal.entries
                if entry.status.value == "VERIFIED"
            )

            failed = sum(
                1
                for entry in journal.entries
                if entry.status.value == "FAILED"
            )

            print()
            print("Maintenance Complete")
            print("═══════════════════")
            print()
            print(
                f"Verified : {verified}"
            )
            print(
                f"Failed   : {failed}"
            )

            print_maintenance_certificate(
                journal
            )

            input(
                "\nPress Enter to continue..."
            )
