from deckflix_app.metadata.models import MediaMetadata

from .ranking import quality_score


def compare_quality(
    existing: MediaMetadata,
    incoming: MediaMetadata,
) -> int:
    """
    Returns:

      1  -> incoming is better
      0  -> equal
     -1  -> existing is better
    """

    old_score = quality_score(existing)
    new_score = quality_score(incoming)

    if new_score > old_score:
        return 1

    if new_score < old_score:
        return -1

    return 0
