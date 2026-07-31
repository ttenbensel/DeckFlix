from pathlib import Path

VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".m4v",
    ".mov",
}


def scan_directory(root: str | Path) -> list[Path]:
    root = Path(root)

    files: list[Path] = []

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            files.append(path)

    return sorted(files)
