from pathlib import Path

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
    print("[C] Clear Queue")
    print("[B] Back")
    print()

    choice = input("Select option: ").strip().lower()

   if choice == "c":
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
