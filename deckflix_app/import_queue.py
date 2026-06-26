from collections import Counter

from deckflix_app.media import inspect_media
from deckflix_app.quality import (
    best_existing_match,
    compare_quality,
)


def build_import_queue(comparison, library_files):
    """
    Build an approval queue.

    Nothing is modified.
    Only recommendations are produced.
    """

    library_media = [
        inspect_media(file)
        for file in library_files
    ]

    queue = []

    # New media
    for item in comparison["new_media"]:
        queue.append({
            "media": item,
            "status": "NEW",
            "action": "IMPORT",
            "reason": "Not found in library",
        })

    # Existing media
    for item in comparison["duplicates"]:

        existing = best_existing_match(
            item,
            library_media,
        )

        if existing:
            decision = compare_quality(
                item,
                existing,
            )

            queue.append({
                "media": item,
                "status": "EXISTS",
                "action": decision["action"],
                "reason": decision["reason"],
                "existing": existing,
                "comparison": decision,
            })

        else:
            queue.append({
                "media": item,
                "status": "EXISTS",
                "action": "REVIEW",
                "reason": "Unable to compare quality",
            })

    return queue


def queue_summary(queue):
    actions = Counter(
        item["action"]
        for item in queue
    )

    return {
        "total": len(queue),
        "import": actions.get("IMPORT", 0),
        "review": actions.get("REVIEW", 0),
        "replace": actions.get("REPLACE", 0),
        "keep": actions.get("KEEP_EXISTING", 0),
    }
