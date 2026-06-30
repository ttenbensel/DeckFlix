from pathlib import Path

from deckflix_app.repair_engine import quarantine_folder, QUARANTINE
from deckflix_app.repair_log import write_log
from deckflix_app.repair_queue import (
    items,
    clear,
    estimated_recovery,
)


def show_repair_queue():
    queue = items()

    print()
    print("Repair Queue")
    print("════════════")
    print()

    if not queue:
        print("Repair queue is empty.")
        input("\nPress Enter to return...")
        return

    print(f"Items Queued       : {len(queue)}")
    print(f"Estimated Recovery : {estimated_recovery():.2f} GB")
    print()

    for index, folder in enumerate(queue, start=1):
        print(f"{index}. {Path(folder).name}")

    print()
    print("[R] Run Repairs")
    print("[C] Clear Queue")
    print("[B] Back")
    print()

    choice = input("Select option: ").strip().lower()

    if choice == "b":
        return

    if choice == "c":
        confirm_clear(queue)
        return

    if choice == "r":
        run_repair_queue(queue)


def confirm_clear(queue):
    print()
    print("Clear Repair Queue")
    print("──────────────────")
    print()
    print(f"This will remove {len(queue)} item(s) from the queue.")
    print("No files will be moved or deleted.")
    print()

    confirm = input("Continue? [Y/N]: ").strip().lower()

    if confirm == "y":
        clear()
        print()
        print("✓ Repair queue cleared.")
    else:
        print()
        print("Queue unchanged.")

    input("\nPress Enter to return...")


def run_repair_queue(queue):
    print()
    print("⚠ Confirm Quarantine")
    print("════════════════════")
    print()
    print(f"Folders to move     : {len(queue)}")
    print(f"Estimated Recovery  : {estimated_recovery():.2f} GB")
    print()
    print("Destination")
    print("───────────")
    print(QUARANTINE)
    print()
    print("Safety")
    print("──────")
    print("✓ Nothing will be deleted")
    print("✓ Folders can be restored from quarantine")
    print()

    confirm = input("Continue? [Y/N]: ").strip().lower()

    if confirm != "y":
        print()
        print("Repair cancelled.")
        input("\nPress Enter to return...")
        return

    print()
    print("Running Repairs")
    print("═══════════════")
    print()

    success_count = 0
    fail_count = 0

    for folder in queue:
        result = quarantine_folder(folder)

        write_log(
            "Quarantine",
            result["source"],
            result["destination"],
            result["message"],
        )

        if result["success"]:
            success_count += 1
            print(f"✓ {Path(folder).name}")
        else:
            fail_count += 1
            print(f"✗ {Path(folder).name}")
            print(f"  {result['message']}")

    if fail_count == 0:
        clear()

    print()
    print("Repair Summary")
    print("──────────────")
    print(f"Moved to quarantine : {success_count}")
    print(f"Failed              : {fail_count}")
    print()
    print("Nothing has been deleted.")
    print()

    input("Press Enter to return...")
