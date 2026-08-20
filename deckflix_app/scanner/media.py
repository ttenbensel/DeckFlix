from pathlib import Path

from deckflix_app.media import (
    SPECIAL_X_PATTERN,
    inspect_media,
)
from deckflix_app.metadata.episode_catalog import (
    resolve_title_only_episode,
)
from deckflix_app.metadata.models import (
    MediaMetadata,
)
from deckflix_app.metadata.parser import (
    parse_filename,
)
from deckflix_app.metadata.patterns import (
    TV_PATTERN,
)

from .filesystem import scan_directory


def _known(value: str | None) -> str | None:
    if value is None:
        return None

    if value.casefold() == "unknown":
        return None

    return value


def _metadata_from_inspected(
    info,
) -> MediaMetadata:
    return MediaMetadata(
        media_type=info.media_type,
        title=info.title,
        content_type=(
            "episode"
            if info.media_type == "tv"
            else "movie"
        ),
        year=info.year,
        season=info.season,
        episode=info.episode,
        resolution=_known(
            info.resolution
        ),
        source=_known(
            info.source
        ),
        video_codec=_known(
            info.codec
        ),
        container=(
            info.path.suffix
            .lstrip(".")
            .lower()
        ),
        path=info.path,
        size=(
            info.path.stat().st_size
            if info.path.exists()
            else 0
        ),
    )


def _metadata_from_filename(
    file: Path,
) -> MediaMetadata:
    parsed = parse_filename(
        file.name
    )

    parsed.path = file

    try:
        parsed.size = (
            file.stat().st_size
        )
    except OSError:
        parsed.size = 0

    return parsed


def _metadata_from_extra(
    path: Path,
) -> MediaMetadata | None:
    """
    Recognise a TV series extra from its directory context.

    The real shuttle currently contains structures such as:

        Series Name/
            Release or Season Folder/
                Extras/
                    file.mkv

    The series identity is therefore the directory two levels
    above the Extras directory.

    Extras are classified as TV content rather than movies.

    Episode numbers embedded in an extra filename must not cause
    the file to become a normal TV episode.
    """
    parts = path.parts

    extras_index = None

    for index in range(
        len(parts) - 1,
        -1,
        -1,
    ):
        if parts[index].casefold() == "extras":
            extras_index = index
            break

    if extras_index is None:
        return None

    if extras_index < 2:
        return None

    series_name = parts[
        extras_index - 2
    ]

    if not series_name:
        return None

    try:
        size = path.stat().st_size
    except OSError:
        size = 0

    return MediaMetadata(
        media_type="tv",
        title=series_name,
        content_type="extra",
        year=None,
        season=None,
        episode=None,
        resolution=None,
        source=None,
        video_codec=None,
        container=(
            path.suffix
            .lstrip(".")
            .lower()
        ),
        path=path,
        size=size,
    )


def _metadata_from_special_filename(
    path: Path,
    parsed: MediaMetadata,
) -> MediaMetadata | None:
    """
    Correct the identity of explicit SxxE00-style TV specials.

    parse_filename() correctly identifies these as TV specials,
    but its title is derived from the complete filename prefix.

    Specials deliberately retain no normal season/episode
    assignment. Their destination routing is handled separately
    as <TV root>/<Series>/Specials/.
    """
    if (
        parsed.media_type != "tv"
        or parsed.content_type != "special"
    ):
        return None

    match = TV_PATTERN.search(
        path.stem
    )

    if match is None:
        return None

    title = path.stem[
        :match.start()
    ]

    title = title.replace(
        ".",
        " ",
    )

    title = title.replace(
        "_",
        " ",
    )

    title = " ".join(
        title.split()
    ).strip()

    if not title:
        return None

    return MediaMetadata(
        media_type="tv",
        title=title,
        content_type="special",
        year=parsed.year,
        season=None,
        episode=None,
        resolution=parsed.resolution,
        source=parsed.source,
        video_codec=parsed.video_codec,
        container=parsed.container,
        path=path,
        size=parsed.size,
    )


def _metadata_from_title_catalog(
    path: Path,
    *,
    inspected,
) -> MediaMetadata | None:
    """
    Promote a title-only file to a TV episode only when a
    trusted catalogue provides an exact identity.

    The candidate title comes directly from the filename stem.

    This is important because inspect_media() deliberately falls
    back conservatively when a Season directory contains a file
    with no numeric episode marker. Its fallback title therefore
    must not be treated as the episode title.

    Unknown titles remain unresolved rather than being guessed.
    """
    identity = resolve_title_only_episode(
        path,
        candidate_title=path.stem,
    )

    if identity is None:
        return None

    try:
        size = path.stat().st_size
    except OSError:
        size = 0

    return MediaMetadata(
        media_type="tv",
        title=identity.title,
        content_type="episode",
        year=None,
        season=identity.season,
        episode=identity.episode,
        resolution=_known(
            inspected.resolution
        ),
        source=_known(
            inspected.source
        ),
        video_codec=_known(
            inspected.codec
        ),
        container=(
            path.suffix
            .lstrip(".")
            .lower()
        ),
        path=path,
        size=size,
    )


def metadata_from_file(
    file: str | Path,
) -> MediaMetadata:
    """
    Parse one existing library file using DeckFlix's canonical,
    conservative identity rules.

    Resolution order:

      1. explicit TV Extras;
      2. contextual/legacy TV detection;
      3. conservative SxxXyy handling;
      4. trusted title-only episode catalogue;
      5. legacy series-specific Extras compatibility;
      6. filename parser;
      7. explicit SxxE00 correction;
      8. ordinary movie fallback.

    Trusted title resolution is exact and fail-closed. It never
    uses directory ordering, fuzzy matching, or guessed episode
    numbers.
    """
    path = Path(file)

    extra_metadata = _metadata_from_extra(
        path
    )

    if extra_metadata is not None:
        return extra_metadata

    inspected = inspect_media(
        path
    )

    if inspected.media_type == "tv":
        return _metadata_from_inspected(
            inspected
        )

    if SPECIAL_X_PATTERN.search(
        path.stem
    ):
        return _metadata_from_inspected(
            inspected
        )

    title_catalog_metadata = (
        _metadata_from_title_catalog(
            path,
            inspected=inspected,
        )
    )

    if title_catalog_metadata is not None:
        return title_catalog_metadata

    if (
        inspected.title
        .casefold()
        .endswith(" extras")
    ):
        return _metadata_from_inspected(
            inspected
        )

    filename_metadata = (
        _metadata_from_filename(
            path
        )
    )

    special_metadata = (
        _metadata_from_special_filename(
            path,
            filename_metadata,
        )
    )

    if special_metadata is not None:
        return special_metadata

    if (
        filename_metadata.media_type
        == "tv"
    ):
        return filename_metadata

    return filename_metadata


def scan_media(
    root: str | Path,
) -> list[MediaMetadata]:
    """
    Read-only scan of video media using DeckFlix's
    combined canonical parsing behaviour.
    """
    return [
        metadata_from_file(
            file
        )
        for file in scan_directory(
            root
        )
    ]
