from pathlib import Path

from deckflix_app.scanner.media import scan_media

from .duplicates import (
    DuplicateCandidate,
    find_duplicates,
)


def scan_duplicates(
    source: Path,
    destination: Path,
) -> list[DuplicateCandidate]:

    source_media = scan_media(
        source
    )

    destination_media = scan_media(
        destination
    )

    return find_duplicates(
        source_media,
        destination_media,
    )
