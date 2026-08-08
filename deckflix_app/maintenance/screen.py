from pathlib import Path

from deckflix_app.config import load_config

from .planner import plan_misplaced_tv
from .plan import create_plan
from .persistence import (
    save_maintenance_plan,
)
from .runner import run_with_progress


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

    if choice != "a":
        return

    plan = create_plan(
        actions,
    )

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

    print("[E] Approve & Execute")
    print("[S] Save Only")
    print()

    next_action = input(
        "Select option: "
    ).strip().lower()

    if next_action != "e":
        print()
        print(
            "Plan saved. No files have been moved."
        )

        input(
            "\nPress Enter to return..."
        )

        return

    print()
    print("Starting Maintenance Operation")
    print("════════════════════════════")
    print()

    journal_path = (
        config.report_directory
        / "maintenance"
        / f"{plan.id}-journal.json"
    )

    journal = run_with_progress(
        plan,
        journal_path,
    )

    print()
    print("Maintenance Complete")
    print("═══════════════════")
    print()

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

    print(
        f"Verified : {verified}"
    )

    print(
        f"Failed   : {failed}"
    )

    input(
        "\nPress Enter to return..."
    )
