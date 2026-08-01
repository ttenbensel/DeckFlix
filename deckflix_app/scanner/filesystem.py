from pathlib import Path


VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".m4v",
    ".mov",
    ".wmv",
}


def scan_directory(root: str | Path) -> list[Path]:
    root = Path(root)

    if not root.exists():
        return []

    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in VIDEO_EXTENSIONS
    ]

    return sorted(files)


def scan_videos(path: str | Path) -> list[Path]:
    """
    Backward-compatible name used by the original DeckFlix interface.
    """
    return scan_directory(path)


def count_videos(path: str | Path) -> int:
    return len(scan_videos(path))


def folder_size_gb(path: str | Path) -> float:
    total = 0

    for item in scan_videos(path):
        try:
            total += item.stat().st_size
        except OSError:
            continue

    return total / 1024**3
