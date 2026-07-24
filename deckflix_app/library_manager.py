from collections import Counter, defaultdict
from pathlib import Path
import shutil

from deckflix_app.media import inspect_media
from deckflix_app.scanner import scan_videos
from deckflix_app.config.config import (
    get_enabled_libraries,
    get_shuttle_path,
)

def scan_library(movies_path, tv_path):
    movie_files = scan_videos(movies_path)
    tv_files = scan_videos(tv_path)

    movie_items = [
        inspect_media(file)
        for file in movie_files
    ]

    tv_items = [
        inspect_media(file)
        for file in tv_files
    ]

    return {
        "movie_files": movie_files,
        "tv_files": tv_files,
        "movie_items": movie_items,
        "tv_items": tv_items,
    }


def count_by_quality(media_items):
    counts = Counter()

    for item in media_items:
        if item.resolution == "unknown":
            counts["unknown"] += 1
        else:
            counts[item.resolution] += 1

    return counts


def find_duplicate_keys(media_items):
    groups = defaultdict(list)

    for item in media_items:
        groups[item.key].append(item)

    return {
        key: items
        for key, items in groups.items()
        if key and len(items) > 1
    }


def find_unknown_quality(media_items):
    return [
        item
        for item in media_items
        if item.resolution == "unknown"
    ]


def find_missing_year_movies(media_items):
    return [
        item
        for item in media_items
        if item.media_type == "movie" and item.year is None
    ]


def library_summary(movies_path, tv_path):
    scan = scan_library(movies_path, tv_path)

    all_items = scan["movie_items"] + scan["tv_items"]

    movie_duplicates = find_duplicate_keys(scan["movie_items"])
    tv_duplicates = find_duplicate_keys(scan["tv_items"])

    return {
        "movies_total": len(scan["movie_items"]),
        "tv_total": len(scan["tv_items"]),
        "movie_duplicates": movie_duplicates,
        "tv_duplicates": tv_duplicates,
        "quality_counts": count_by_quality(all_items),
        "unknown_quality": find_unknown_quality(all_items),
        "missing_year_movies": find_missing_year_movies(scan["movie_items"]),
    }

def calculate_health_score(summary):
    """
    Calculate a balanced library health score.

    This first version is deliberately conservative because
    DeckFlix is still learning the library.
    """

    score = 100

    movie_duplicate_penalty = min(len(summary["movie_duplicates"]) // 5, 12)
    tv_duplicate_penalty = min(len(summary["tv_duplicates"]) // 3, 8)
    missing_year_penalty = min(len(summary["missing_year_movies"]) // 3, 8)
    unknown_quality_penalty = min(len(summary["unknown_quality"]) // 25, 15)

    score -= movie_duplicate_penalty
    score -= tv_duplicate_penalty
    score -= missing_year_penalty
    score -= unknown_quality_penalty

    return max(score, 0)

def duplicate_examples(duplicates, limit=10):
    """
    Return readable duplicate titles.

    Sort alphabetically and limit the output so the
    Library Health screen stays tidy.
    """

    examples = []

    for key in sorted(duplicates.keys()):
        if isinstance(key, tuple):
            title = key[0]

            if len(key) > 1 and key[1]:
                title = f"{title} ({key[1]})"
        else:
            title = str(key)

        examples.append(title)

    return examples[:limit]
def get_library_status(library):
    """
    Return storage and availability information for one configured library.
    """

    root = Path(library["path"])
    movie_path = root / "movie"
    tv_path = root / "tv"
    online = root.exists() and root.is_dir()

    status = {
        "name": library["name"],
        "path": root,
        "movie_path": movie_path,
        "tv_path": tv_path,
        "enabled": library.get("enabled", True),
        "online": online,
        "total_bytes": 0,
        "used_bytes": 0,
        "free_bytes": 0,
        "used_percent": 0.0,
    }

    if not online:
        return status

    usage = shutil.disk_usage(root)

    status["total_bytes"] = usage.total
    status["used_bytes"] = usage.used
    status["free_bytes"] = usage.free

    if usage.total:
        status["used_percent"] = round(
            usage.used / usage.total * 100,
            1,
        )

    return status


def get_all_library_statuses():
    """
    Return status information for every enabled library.
    """

    return [
        get_library_status(library)
        for library in get_enabled_libraries()
    ]


def best_import_library(required_bytes=0):
    """
    Select the online enabled library with the most available space.

    Return None when no library has enough free space.
    """

    candidates = [
        status
        for status in get_all_library_statuses()
        if status["online"] and status["free_bytes"] >= required_bytes
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda status: status["free_bytes"],
    )


def shuttle_connected():
    """
    Return True when the configured shuttle path is available.
    """

    shuttle = get_shuttle_path()
    return shuttle.exists() and shuttle.is_dir()


def scan_all_libraries():
    """
    Scan every enabled, online library and return combined results.
    """

    results = {}

    for library in get_enabled_libraries():
        status = get_library_status(library)

        if not status["online"]:
            results[library["name"]] = {
                "status": status,
                "scan": None,
            }
            continue

        results[library["name"]] = {
            "status": status,
            "scan": scan_library(
                status["movie_path"],
                status["tv_path"],
            ),
        }

    return results
