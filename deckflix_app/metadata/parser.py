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


def parse_filename(
    filename: str,
    context: str | None = None,
) -> MediaMetadata:
    path = Path(filename)

    stem = path.stem
    container = path.suffix.lstrip(".").lower()
    search_text = f"{stem} {context or ''}"

    resolution = None
    source = None
    codec = None

    if match := RESOLUTION_PATTERN.search(search_text):
        resolution = match.group(1)

    if match := SOURCE_PATTERN.search(search_text):
        source = match.group(1)

    if match := CODEC_PATTERN.search(search_text):
        codec = match.group(1)

    tv_match = TV_PATTERN.search(stem)

    if tv_match:
        groups = tv_match.groupdict()

        season = int(
            groups["s1"]
            or groups["s2"]
            or groups["s3"]
        )

        episode = int(
            groups["e1"]
            or groups["e2"]
            or groups["e3"]
        )

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

    years = YEAR_PATTERN.findall(stem)

    if years:
        matches = list(YEAR_PATTERN.finditer(stem))

        first_year = matches[0]

        # Handle numeric movie titles:
        # Example:
        # 1917.2019.1080p.BluRay.mkv
        if (
            first_year.start() == 0
            and len(matches) > 1
        ):
            title = stem[:first_year.end()]
            year = int(matches[1].group(1))

        else:
            year = int(first_year.group(1))
            title = stem[:first_year.start()].rstrip(" ([{-_.")

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
