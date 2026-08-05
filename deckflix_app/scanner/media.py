from pathlib import Path

from deckflix_app.metadata.parser import parse_filename

from .filesystem import scan_directory


def scan_media(root: str | Path):
    media = []

    for file in scan_directory(root):
        context = " ".join(
            part.name
            for part in file.parents
            if part.name
        )

        item = parse_filename(
            file.name,
            context=context,
        )

        item.path = file
        item.size = file.stat().st_size

        media.append(item)

    return media
