from pathlib import Path
import shutil
from deckflix_app.quarantine_metadata import write_metadata


QUARANTINE = Path("/mnt/dest4tb/deckflix-quarantine")


def build_repair_preview(folder):
    """
    Build a repair preview.

    Nothing is moved or deleted by this function.
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


def quarantine_folder(folder):
    """
    Move a folder into the DeckFlix quarantine folder.

    This does not delete anything.
    """

    source = Path(folder)
    destination = QUARANTINE / source.name

    if not source.exists():
        return {
            "success": False,
            "message": "Source folder does not exist.",
            "source": source,
            "destination": destination,
        }

    if destination.exists():
        return {
            "success": False,
            "message": "Destination already exists in quarantine.",
            "source": source,
            "destination": destination,
        }

    QUARANTINE.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    
    write_metadata(
        destination,
        reason="Duplicate Release",
    )
    
    return {
        "success": True,
        "message": "Folder moved to quarantine.",
        "source": source,
        "destination": destination,
    }
