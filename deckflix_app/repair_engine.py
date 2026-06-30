from pathlib import Path


QUARANTINE = Path("/mnt/dest4tb/deckflix-quarantine")


def build_repair_preview(folder):
    """
    Build a dry-run repair preview.

    Nothing is moved or deleted.
    """

    folder = Path(folder)

    return {
        "source": folder,
        "destination": QUARANTINE / folder.name,
        "action": "Move folder to quarantine",
        "dry_run": True,
    }


def show_repair_preview(folder):
    preview = build_repair_preview(folder)

    print()
    print("Repair Preview")
    print("══════════════")
    print()

    print("Selected Folder")
    print("───────────────")
    print(preview["source"])
    print()

    print("Destination")
    print("───────────")
    print(preview["destination"])
    print()

    print("Action")
    print("──────")
    print(preview["action"])
    print()

    print("Safety")
    print("──────")
    print("✓ Dry Run")
    print("✓ No files moved")
    print("✓ No files deleted")
    print()

    input("Press Enter to return...")
