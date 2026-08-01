from pathlib import Path
import shutil


def atomic_move(temp_file: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(
        temp_file,
        destination,
    )

    temp_file.unlink()

    return destination
