RESOLUTION_RANK = {
    "unknown": 0,
    "480p": 1,
    "720p": 2,
    "1080p": 3,
    "2160p": 4,
}

SOURCE_RANK = {
    "unknown": 0,
    "Screener": 1,
    "HDRip": 2,
    "WEBRip": 3,
    "WEB-DL": 4,
    "BluRay": 5,
}

CODEC_RANK = {
    "unknown": 0,
    "H264": 1,
    "HEVC": 2,
}


def rank_media(item):
    """
    Produce a deterministic ranking for one media item.

    Higher quality score, source, resolution and codec are preferred.
    File size is only used as the final tie-breaker, where smaller wins.
    """

    return (
        item.quality_score,
        SOURCE_RANK.get(item.source, 0),
        RESOLUTION_RANK.get(item.resolution, 0),
        CODEC_RANK.get(item.codec, 0),
        -item.size,
    )


def recommendation_reasons(keep, others):
    """
    Explain why DeckFlix selected this version.

    Only include reasons that actually distinguish the chosen file
    from the alternatives.
    """

    reasons = []

    # Higher quality score
    best_other = max(item.quality_score for item in others)

    if keep.quality_score > best_other:
        reasons.append(
            f"Higher quality score ({keep.quality_score} vs {best_other})"
        )

    # Better source
    best_source = max(
        SOURCE_RANK.get(item.source, 0)
        for item in others
    )

    if SOURCE_RANK.get(keep.source, 0) > best_source:
        reasons.append(f"Better source ({keep.source})")

    # Better resolution
    best_resolution = max(
        RESOLUTION_RANK.get(item.resolution, 0)
        for item in others
    )

    if RESOLUTION_RANK.get(keep.resolution, 0) > best_resolution:
        reasons.append(f"Higher resolution ({keep.resolution})")

    # Better codec
    best_codec = max(
        CODEC_RANK.get(item.codec, 0)
        for item in others
    )

    if CODEC_RANK.get(keep.codec, 0) > best_codec:
        reasons.append(f"Better codec ({keep.codec})")

    # Smaller file if quality is equal
    if (
        keep.size < min(item.size for item in others)
        and keep.quality_score >= best_other
    ):
        reasons.append("Smaller file with no quality loss")

    # REPACK bonus
    if "repack" in str(keep.path).lower():
        reasons.append("REPACK release")

    if not reasons:
        reasons.append("Manual review recommended")

    return reasons

def recommend_duplicate_group(items):
    """
    Recommend which duplicate candidate to keep.

    This function is advisory only. It never moves or deletes files.
    """

    if len(items) < 2:
        raise ValueError("At least two media items are required.")

    ranked = sorted(
        items,
        key=rank_media,
        reverse=True,
    )

    keep = ranked[0]
    review = ranked[1:]

    return {
        "keep": keep,
        "review": review,
        "reasons": recommendation_reasons(keep, review),
        "confidence": recommendation_confidence(keep, review),
    }


def recommendation_confidence(keep, others):
    """
    Return a conservative confidence percentage.
    """

    confidence = 50

    if keep.source != "unknown":
        confidence += 15

    if keep.resolution != "unknown":
        confidence += 10

    if keep.codec != "unknown":
        confidence += 5

    if all(keep.quality_score > item.quality_score for item in others):
        confidence += 15

    if all(keep.size != item.size for item in others):
        confidence += 5

    return min(confidence, 95)
