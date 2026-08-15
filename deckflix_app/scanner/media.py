from pathlib import Path

from deckflix_app.media import (
    SPECIAL_X_PATTERN,
    inspect_media,
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

    # We need:
    #
    #   Series / Release / Extras / file
    #
    # so the Extras directory must have at least two parents.
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
    For example:

        South.Park.S24E00.The.Pandemic.Special.mkv

    would otherwise become:

        South Park S24E00 The Pandemic

    The series identity is the text before the SxxE00 marker:

        South Park

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


def metadata_from_file(
    file: str | Path,
) -> MediaMetadata:
    """
    Parse one existing library file using both DeckFlix
    parser generations conservatively.

    inspect_media() remains authoritative for:
      - contextual TV detection,
      - release-folder TV detection,
      - legacy Part/Episode formats,
      - S00 parent specials,
      - special SxxXyy identities.

    Explicit TV Extras are handled before the legacy
    series-specific Extras compatibility behaviour so that
    import routing sees them as TV content.

    Explicit SxxE00 specials are corrected after filename
    parsing so their identity is the parent series rather
    than the filename's episode-zero title.

    parse_filename() is used to improve ordinary movie
    title/year extraction and to recognise explicit SxxE00-style
    episode filenames that inspect_media() intentionally treats
    conservatively.
    """
    path = Path(file)

    # Handle Extras before inspect_media() can convert them
    # into the legacy "Series Extras" movie representation.
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

    # Preserve inspect_media()'s deliberately special
    # treatment of SxxXyy.
    if SPECIAL_X_PATTERN.search(
        path.stem
    ):
        return _metadata_from_inspected(
            inspected
        )

    # Preserve series-specific Extras identities for any
    # legacy cases not recognised by the directory-contextual
    # extra detector.
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

    # Correct explicit SxxE00 TV specials before the
    # ordinary TV/movie fallback logic.
    special_metadata = (
        _metadata_from_special_filename(
            path,
            filename_metadata,
        )
    )

    if special_metadata is not None:
        return special_metadata

    # This catches explicit S24E00 and similar cases which
    # the legacy parser intentionally excludes from its
    # ordinary positive-episode detector.
    if (
        filename_metadata.media_type
        == "tv"
    ):
        return filename_metadata

    # For ordinary movie files, filename parsing is generally
    # more precise than deriving identity from the immediate
    # parent directory.
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
