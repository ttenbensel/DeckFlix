from pathlib import Path

VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".mov", ".wmv", ".m4v"}


def scan_videos(path):
    path = Path(path)

    if not path.exists():
        return []

    return [
        item
        for item in path.rglob("*")
        if item.is_file() and item.suffix.lower() in VIDEO_EXTS
    ]


def count_videos(path):
    return len(scan_videos(path))


def folder_size_gb(path):
    total = 0

    for item in scan_videos(path):
        try:
            total += item.stat().st_size
        except Exception:
            pass

    return total / 1024**3
