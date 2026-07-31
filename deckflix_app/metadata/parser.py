from pathlib import Path

from .models import MediaMetadata
from .patterns import (
    CODEC_PATTERN,
    RESOLUTION_PATTERN,
    SOURCE_PATTERN,
    TV_PATTERN,
    YEAR_PATTERN,
)


def _clean_title(title: str) -> str:
    title = title.replace(".", " ")
    title = title.replace("_", " ")
    return " ".join(title.split()).strip()


def parse_filename(filename: str) -> MediaMetadata:
    path = Path(filename)

    stem = path.stem
    container = path.suffix.lstrip(".").lower()

    resolution = None
    source = None
    codec = None

    if match := RESOLUTION_PATTERN.search(stem):
        resolution = match.group(1)

    if match := SOURCE_PATTERN.search(stem):
        source = match.group(1)

    if match := CODEC_PATTERN.search(stem):
        codec = match.group(1)

    tv_match = TV_PATTERN.search(stem)

    if tv_match:
        season = int(tv_match.group(1))
        episode = int(tv_match.group(2))

        title = _clean_title(stem[:tv_match.start()])

        return MediaMetadata(
            media_type="tv",
            title=title,
            season=season,
            episode=episode,
            resolution=resolution,
            source=source,
            video_codec=codec,
            container=container,
        )

    year = None
    title = stem

    if match := YEAR_PATTERN.search(stem):
        year = int(match.group(1))
        title = stem[:match.start()].rstrip(" ([{-_.")

    title = _clean_title(title)

    return MediaMetadata(
        media_type="movie",
        title=title,
        year=year,
        resolution=resolution,
        source=source,
        video_codec=codec,
        container=container,
    )
