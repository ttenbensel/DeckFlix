from collections import Counter, defaultdict
from pathlib import Path

from deckflix_app.media import inspect_media
from deckflix_app.scanner import scan_videos


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
    Calculate a simple library health score.

    Starts at 100 and deducts points for issues.
    """

    score = 100

    score -= min(len(summary["movie_duplicates"]), 20)
    score -= min(len(summary["tv_duplicates"]), 10)
    score -= min(len(summary["missing_year_movies"]), 10)
    score -= min(len(summary["unknown_quality"]) // 10, 20)

    return max(score, 0)
