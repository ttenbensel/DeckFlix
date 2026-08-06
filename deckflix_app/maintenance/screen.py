from pathlib import Path

from deckflix_app.config import load_config

from .planner import plan_misplaced_tv
from .plan import create_plan
from .persistence import save_maintenance_plan


def show_repair_preview(
    movies_path: Path,
    tv_path: Path,
):
    actions = plan_misplaced_tv(
        movies_path,
        tv_path,
    )

    print()
    print("Review & Approve Repairs")
    print("═══════════════════════")
    print()

    if not actions:
        print("No repairs detected.")
        input("\nPress Enter to return...")
        return

    print(
        f"Misplaced TV Content : {len(actions)} files"
    )
    print()

    print("Examples")
    print("────────")

    for action in actions[:10]:
        print()
        print(action.source.name)
        print("FROM:")
        print(action.source.parent)
        print("TO:")
        print(action.destination.parent)

    print()
    print("[A] Create Maintenance Plan")
    print("[B] Back")
    print()

    choice = input(
        "Select option: "
    ).strip().lower()

    if choice == "a":
        plan = create_plan(actions)

        config = load_config()

        plan_path = (
            config.report_directory
            / "maintenance"
            / f"{plan.id}.json"
        )

        save_maintenance_plan(
            plan,
            plan_path,
        )

        print()
        print("Maintenance Plan Created")
        print("═══════════════════════")
        print()
        print(f"ID      : {plan.id}")
        print(f"Actions : {plan.total_actions}")
        print(f"State   : {plan.state.value}")
        print()
        print("Saved:")
        print(plan_path)
        print()
        print(
            "No files have been moved."
        )

    input(
        "\nPress Enter to return..."
    )
