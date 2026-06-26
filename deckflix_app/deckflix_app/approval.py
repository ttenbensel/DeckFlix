def approve_imports(queue):
    """
    Return only items approved for import.

    For now, every IMPORT action is automatically approved.
    Later this will become an interactive approval screen.
    """

    approved = []

    for item in queue:
        if item["action"] == "IMPORT":
            approved.append(item)

    return approved


def approval_summary(approved):
    return {
        "approved": len(approved),
    }
