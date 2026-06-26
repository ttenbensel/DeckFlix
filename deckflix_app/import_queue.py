from collections import Counter


def build_import_queue(comparison):
    """
    Convert the comparison results into an approval queue.

    Nothing is modified here.
    This module only prepares recommendations.
    """

    queue = []

    for item in comparison["new_media"]:
        queue.append({
            "media": item,
            "status": "NEW",
            "action": "IMPORT",
            "reason": "Not found in library",
        })

    for item in comparison["duplicates"]:
        queue.append({
            "media": item,
            "status": "EXISTS",
            "action": "REVIEW",
            "reason": "Matching title already exists",
        })

    return queue


def queue_summary(queue):
    actions = Counter(item["action"] for item in queue)

    return {
        "total": len(queue),
        "import": actions.get("IMPORT", 0),
        "review": actions.get("REVIEW", 0),
        "replace": actions.get("REPLACE", 0),
        "ignore": actions.get("IGNORE", 0),
    }
