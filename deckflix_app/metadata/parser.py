from pathlib import Path
import re

from .models import MediaMetadata
from .patterns import (
    CODEC_PATTERN,
    EXTRA_PATTERN,
    RESOLUTION_PATTERN,
    SCENE_EPISODE_PATTERN,
    SOURCE_PATTERN,
    SPECIAL_PATTERN,
    TV_CONTEXT_PATTERN,
    TV_PATTERN,
    YEAR_PATTERN,
)


def _clean_title(title: str) -> str:
    title = title.replace(".", " ")
    title = title.replace("_", " ")
    return " ".join(title.split()).strip()


def _clean_tv_title(title: str) -> str:
    title = re.sub(
        r"\bseason[ ._-]*\d+\b",
        "",
        title,
        flags=re.IGNORECASE,
    )

    title = re.sub(
        r"\bseries[ ._-]*\d+\b",
        "",
        title,
        flags=re.IGNORECASE,
    )

    title = re.sub(
        r"\b(christmas|holiday|halloween)\s+specials?\b.*$",
        "",
        title,
        flags=re.IGNORECASE,
    )

    title = re.sub(
        r"\b(special|specials|extra|extras)\b.*$",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return _clean_title(title)


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

    if EXTRA_PATTERN.search(search_text):
        return MediaMetadata(
            media_type="tv",
            title=_clean_tv_title(stem),
            content_type="extra",
            resolution=resolution,
            source=source,
            video_codec=codec,
            container=container,
        )

    tv_context = (
        TV_PATTERN.search(stem)
        or (
            context
            and TV_CONTEXT_PATTERN.search(context)
        )
    )

    is_special_title = (
        " special" in stem.lower()
        or " specials" in stem.lower()
    )

    if (
        SPECIAL_PATTERN.search(search_text)
        and (
            tv_context
            or is_special_title
        )
    ):
        return MediaMetadata(
            media_type="tv",
            title=_clean_tv_title(stem),
            content_type="special",
            resolution=resolution,
            source=source,
            video_codec=codec,
            container=container,
        )

    tv_match = TV_PATTERN.search(stem)

    if tv_match:
        groups = tv_match.groupdict()

        season = int(
            groups.get("s1")
            or groups.get("s2")
            or groups.get("s3")
            or groups.get("s4")
            or groups.get("s5")
            or groups.get("s6")
            or groups.get("s7")
        )

        episode = int(
            groups.get("e1")
            or groups.get("e2")
            or groups.get("e3")
            or groups.get("e4")
            or groups.get("e5")
            or groups.get("e6")
            or groups.get("e7")
        )

        return MediaMetadata(
            media_type="tv",
            title=_clean_title(
                stem[:tv_match.start()]
            ),
            content_type="episode",
            season=season,
            episode=episode,
            resolution=resolution,
            source=source,
            video_codec=codec,
            container=container,
        )

    if context and TV_CONTEXT_PATTERN.search(context):

        season_match = re.search(
            r"[Ss]eason[ ._-]*(\d+)",
            context,
            re.IGNORECASE,
        )

        scene_match = SCENE_EPISODE_PATTERN.search(stem)

        if season_match and scene_match:

            season = int(
                season_match.group(1)
            )

            code = scene_match.group(
                "scene_episode"
            )

            episode = int(code[-2:])

            return MediaMetadata(
                media_type="tv",
                title=_clean_title(
                    stem[:scene_match.start()]
                ),
                content_type="episode",
                season=season,
                episode=episode,
                resolution=resolution,
                source=source,
                video_codec=codec,
                container=container,
            )

        return MediaMetadata(
            media_type="tv",
            title=_clean_title(stem),
            content_type="episode",
            resolution=resolution,
            source=source,
            video_codec=codec,
            container=container,
        )

    year = None
    title = stem

    years = YEAR_PATTERN.findall(stem)

    if years:

        matches = list(
            YEAR_PATTERN.finditer(stem)
        )

        first_year = matches[0]

        if (
            first_year.start() == 0
            and len(matches) > 1
        ):
            title = stem[:first_year.end()]
            year = int(
                matches[1].group(1)
            )

        else:
            year = int(
                first_year.group(1)
            )

            title = stem[
                :first_year.start()
            ].rstrip(" ([{-_.")

    return MediaMetadata(
        media_type="movie",
        title=_clean_title(title),
        content_type="movie",
        year=year,
        resolution=resolution,
        source=source,
        video_codec=codec,
        container=container,
    )
