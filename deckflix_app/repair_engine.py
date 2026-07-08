from pathlib import Path
import shutil

from deckflix_app.quarantine_metadata import (
    metadata_file,
    read_metadata,
    write_metadata,
)
from deckflix_app.config.config import get_quarantine_path

QUARANTINE = get_quarantine_path()

def build_repair_preview(folder):
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
        original_path=source,
        reason="Duplicate Release",
    )

    return {
        "success": True,
        "message": "Folder moved to quarantine.",
        "source": source,
        "destination": destination,
    }


def restore_folder(folder):
    source = Path(folder)
    metadata = read_metadata(source)
    destination = Path(metadata["original_path"])

    if not source.exists():
        return {
            "success": False,
            "message": "Quarantined folder does not exist.",
            "source": source,
            "destination": destination,
        }

    if destination.exists():
        return {
            "success": False,
            "message": "Original destination already exists.",
            "source": source,
            "destination": destination,
        }

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))

    meta = metadata_file(destination)
    old_meta = metadata_file(source)

    if old_meta.exists():
        shutil.move(str(old_meta), str(meta))

    return {
        "success": True,
        "message": "Folder restored from quarantine.",
        "source": source,
        "destination": destination,
    }
