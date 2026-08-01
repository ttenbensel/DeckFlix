def compare_quality(incoming, existing):
    """
    Legacy MediaInfo quality comparison used by the interactive UI.
    """
    incoming_score = incoming.quality_score
    existing_score = existing.quality_score
    difference = incoming_score - existing_score

    if difference >= 15:
        action = "REPLACE"
        reason = "Incoming file appears to be significantly better quality"
    elif difference <= -15:
        action = "KEEP_EXISTING"
        reason = "Existing library file appears to be better quality"
    else:
        action = "REVIEW"
        reason = "Quality appears similar or uncertain"

    return {
        "incoming": incoming,
        "existing": existing,
        "incoming_score": incoming_score,
        "existing_score": existing_score,
        "difference": difference,
        "action": action,
        "reason": reason,
    }


def best_existing_match(incoming, existing_items):
    matches = [
        item
        for item in existing_items
        if item.key == incoming.key
    ]

    if not matches:
        return None

    return max(
        matches,
        key=lambda item: item.quality_score,
    )


def quality_label(media):
    parts = []

    if media.resolution != "unknown":
        parts.append(media.resolution)

    if media.source != "unknown":
        parts.append(media.source)

    if media.codec != "unknown":
        parts.append(media.codec)

    return " ".join(parts) if parts else "unknown quality"
