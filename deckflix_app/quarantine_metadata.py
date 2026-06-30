import json
from datetime import datetime
from pathlib import Path


def metadata_file(folder):
    folder = Path(folder)
    return folder.parent / f"{folder.name}.deckflix.json"


def write_metadata(folder, reason="Duplicate Release"):
    folder = Path(folder)

    data = {
        "original_path": str(folder),
        "quarantined": datetime.now().isoformat(timespec="seconds"),
        "reason": reason,
    }

    with metadata_file(folder).open("w") as f:
        json.dump(data, f, indent=4)


def read_metadata(folder):
    with metadata_file(folder).open() as f:
        return json.load(f)
