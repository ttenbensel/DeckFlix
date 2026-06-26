from pathlib import Path
import shutil

from deckflix_app.scanner import scan_videos
from deckflix_app.media import inspect_media


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
            "media": [],
        }

    files = scan_videos(shuttle)
    media_items = [inspect_media(file) for file in files]

    movies = [
        item
        for item in media_items
        if item.media_type == "movie"
    ]

    tv = [
        item
        for item in media_items
        if item.media_type == "tv"
    ]

    return {
        "connected": True,
        "path": shuttle,
        "storage": storage,
        "files": files,
        "movies": movies,
        "tv": tv,
        "media": media_items,
    }


def compare_to_library(shuttle_media, library_files):
    library_items = [inspect_media(file) for file in library_files]
    library_keys = set(item.key for item in library_items if item.key)

    new_media = []
    duplicates = []

    for item in shuttle_media:
        if item.key in library_keys:
            duplicates.append(item)
        else:
            new_media.append(item)

    return {
        "new_media": new_media,
        "duplicates": duplicates,
    }
