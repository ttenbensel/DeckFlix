from pathlib import Path
import shutil

from deckflix_app.scanner import scan_videos
from deckflix_app.health import clean_title


def is_tv_file(path):
    name = str(path).lower()

    return (
        "s01" in name
        or "s02" in name
        or "s03" in name
        or "s04" in name
        or "s05" in name
        or "season" in name
    )


def get_storage_info(path):
    target = Path(path)

    if not target.exists():
        return {
            "available": False,
            "used_tb": 0,
            "total_tb": 0,
            "free_tb": 0,
        }

    usage = shutil.disk_usage(target)

    return {
        "available": True,
        "used_tb": usage.used / 1024**4,
        "total_tb": usage.total / 1024**4,
        "free_tb": usage.free / 1024**4,
    }


def scan_shuttle(shuttle_path):
    shuttle = Path(shuttle_path)
    storage = get_storage_info(shuttle)

    if not shuttle.exists():
        return {
            "connected": False,
            "path": shuttle,
            "storage": storage,
            "files": [],
            "movies": [],
            "tv": [],
        }

    files = scan_videos(shuttle)
    movies = []
    tv = []

    for file in files:
        if is_tv_file(file):
            tv.append(file)
        else:
            movies.append(file)

    return {
        "connected": True,
        "path": shuttle,
        "storage": storage,
        "files": files,
        "movies": movies,
        "tv": tv,
    }


def compare_to_library(shuttle_files, library_files):
    library_titles = set()

    for file in library_files:
        title = clean_title(Path(file).parent.name)
        if title:
            library_titles.add(title)

    new_media = []
    duplicates = []

    for file in shuttle_files:
        title = clean_title(Path(file).parent.name)

        if title in library_titles:
            duplicates.append(file)
        else:
            new_media.append(file)

    return {
        "new_media": new_media,
        "duplicates": duplicates,
    }
