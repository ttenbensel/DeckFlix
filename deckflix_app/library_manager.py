from collections import Counter, defaultdict

from deckflix_app.scanner import scan_media
from deckflix_app.library.index import media_key


def scan_library(movies_path, tv_path):
    movie_folder_items = scan_media(movies_path)
    tv_folder_items = scan_media(tv_path)

    movie_items = [
        item
        for item in movie_folder_items
        if item.media_type == "movie"
    ]

    misplaced_tv_items = [
        item
        for item in movie_folder_items
        if item.media_type == "tv"
    ]

    tv_items = list(misplaced_tv_items)
    tv_items.extend(tv_folder_items)

    return {
        "movie_items": movie_items,
        "tv_items": tv_items,
        "misplaced_tv_items": misplaced_tv_items,
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
        groups[media_key(item)].append(item)

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
        if item.media_type == "movie"
        and item.year is None
    ]


def find_misplaced_tv(scan):
    return scan["misplaced_tv_items"]


def library_summary(movies_path, tv_path):
    scan = scan_library(
        movies_path,
        tv_path,
    )

    all_items = (
        scan["movie_items"]
        + scan["tv_items"]
    )

    movie_duplicates = find_duplicate_keys(
        scan["movie_items"]
    )

    tv_duplicates = find_duplicate_keys(
        scan["tv_items"]
    )

    return {
        "movies_total": len(scan["movie_items"]),
        "tv_total": len(scan["tv_items"]),
        "movie_duplicates": movie_duplicates,
        "tv_duplicates": tv_duplicates,
        "quality_counts": count_by_quality(all_items),
        "unknown_quality": find_unknown_quality(all_items),
        "missing_year_movies": find_missing_year_movies(
            scan["movie_items"]
        ),
        "misplaced_tv": find_misplaced_tv(scan),
    }


def calculate_health_score(summary):
    """
    Calculate a balanced library health score.

    This first version is deliberately conservative because
    DeckFlix is still learning the library.
    """

    score = 100

    movie_duplicate_penalty = min(
        len(summary["movie_duplicates"]) // 5,
        12,
    )

    tv_duplicate_penalty = min(
        len(summary["tv_duplicates"]) // 3,
        8,
    )

    missing_year_penalty = min(
        len(summary["missing_year_movies"]) // 3,
        8,
    )

    unknown_quality_penalty = min(
        len(summary["unknown_quality"]) // 25,
        15,
    )

    misplaced_tv_penalty = min(
        len(summary["misplaced_tv"]) // 50,
        10,
    )

    score -= movie_duplicate_penalty
    score -= tv_duplicate_penalty
    score -= missing_year_penalty
    score -= unknown_quality_penalty
    score -= misplaced_tv_penalty

    return max(score, 0)


def duplicate_examples(duplicates, limit=10):
    """
    Return readable duplicate titles.

    Supports the current media key format:
    ("movie", title, year)
    ("tv", title, season, episode)
    """

    examples = []

    for key in sorted(duplicates.keys()):
        if isinstance(key, tuple):

            if key[0] == "movie":
                title = key[1]

                if len(key) > 2 and key[2]:
                    title = f"{title} ({key[2]})"

            elif key[0] == "tv":
                title = key[1]

                if len(key) > 3:
                    title = (
                        f"{title} "
                        f"S{key[2]:02d}E{key[3]:02d}"
                    )

            else:
                title = str(key)

        else:
            title = str(key)

        examples.append(title)

    return examples[:limit]
