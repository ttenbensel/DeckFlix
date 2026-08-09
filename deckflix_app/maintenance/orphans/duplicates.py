from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from deckflix_app.library.index import media_key
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.quality.comparator import compare_quality


class DuplicateType(str, Enum):
    DUPLICATE_MEDIA = "DUPLICATE_MEDIA"
    SOURCE_BETTER = "SOURCE_BETTER"
    QUALITY_REVIEW = "QUALITY_REVIEW"


@dataclass(slots=True)
class DuplicateCandidate:
    source: MediaMetadata
    destination: MediaMetadata
    classification: DuplicateType
    reason: str


def compare_duplicate(
    source: MediaMetadata,
    destination: MediaMetadata,
) -> DuplicateCandidate | None:

    if media_key(source) != media_key(destination):
        return None


    result = compare_quality(
        destination,
        source,
    )


    if result == 1:

        return DuplicateCandidate(
            source=source,
            destination=destination,
            classification=(
                DuplicateType.SOURCE_BETTER
            ),
            reason=(
                "Source media appears "
                "higher quality than destination"
            ),
        )


    if result == -1:

        return DuplicateCandidate(
            source=source,
            destination=destination,
            classification=(
                DuplicateType.DUPLICATE_MEDIA
            ),
            reason=(
                "Destination media is "
                "higher quality"
            ),
        )


    return DuplicateCandidate(
        source=source,
        destination=destination,
        classification=(
            DuplicateType.QUALITY_REVIEW
        ),
        reason=(
            "Same media with "
            "similar quality"
        ),
    )


def find_duplicates(
    source_items: list[MediaMetadata],
    destination_items: list[MediaMetadata],
) -> list[DuplicateCandidate]:

    results = []


    destination_map = {
        media_key(item): item
        for item in destination_items
    }


    for source in source_items:

        destination = destination_map.get(
            media_key(source)
        )


        if not destination:
            continue


        result = compare_duplicate(
            source,
            destination,
        )


        if result:
            results.append(
                result
            )


    return results
