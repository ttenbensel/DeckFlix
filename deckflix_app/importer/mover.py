from pathlib import Path


def atomic_move(temp_file: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)

    temp_file.replace(destination)

    return destination
