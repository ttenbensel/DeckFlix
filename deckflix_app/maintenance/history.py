from pathlib import Path

from .manager import MaintenanceManager


def show_maintenance_history(
    directory: Path,
):
    manager = MaintenanceManager(
        directory,
    )

    plans = manager.list_plans()

    print()
    print("Maintenance History")
    print("═══════════════════")
    print()

    if not plans:
        print("No maintenance history found.")
        input(
            "\nPress Enter to return..."
        )
        return

    for plan_path in plans:
        plan = manager.load(
            plan_path,
        )

        if plan is None:
            continue

        print(
            plan.id
        )

        print(
            f"Actions : "
            f"{plan.total_actions}"
        )

        print(
            f"State   : "
            f"{plan.state.value}"
        )

        print()
