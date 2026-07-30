from __future__ import annotations

import re
from pathlib import Path

from deckflix.models import ParsedMedia
from deckflix.parser.cleaner import clean_release_name, clean_title_case


TV_PATTERNS = [
    (
        "sxe",
        re.compile(
            r"""(?ix)
            (?P<show>.*?)
            [ ._\-\[\(]+
            S(?P<season>\d{1,2})
            [ ._-]*
            E(?P<episode>\d{1,3})
            """
        ),
        98,
    ),
    (
        "sx-uppercase",
        re.compile(
            r"""(?ix)
            (?P<show>.*?)
            [ ._\-\[\(]+
            S(?P<season>\d{1,2})
            [ ._-]*
            X(?P<episode>\d{1,3})
            """
        ),
        97,
    ),
    (
        "number-x-number",
        re.compile(
            r"""(?ix)
            (?P<show>.*?)
            [ ._\-\[\(]+
            (?P<season>\d{1,2})
            X(?P<episode>\d{1,3})
            """
        ),
        96,
    ),
]

SEASON_FOLDER = re.compile(
    r"(?ix)^season[ ._-]*(?P<season>\d{1,2})$"
)

EPISODE_ONLY = re.compile(
    r"""(?ix)
    ^(?:episode|ep|e)[ ._-]*
    (?P<episode>\d{1,3})
    \b
    """
)

YEAR_PATTERN = re.compile(
    r"(?<!\d)(?P<year>19\d{2}|20\d{2})(?!\d)"
)

SPECIAL_PATTERN = re.compile(
    r"(?ix)\bS(?P<season>\d{1,2})M(?P<special>\d{1,3})\b"
)


def _show_from_path(path: Path, matched_show: str | None) -> str | None:
    candidate = clean_title_case(matched_show or "")

    if candidate:
        return candidate

    parts = list(path.parts)

    for index, part in enumerate(parts[:-1]):
        if SEASON_FOLDER.match(part) and index > 0:
            return clean_title_case(parts[index - 1])

    if len(parts) >= 2:
        return clean_title_case(parts[-2])

    return None


def parse_media(relative_path: str | Path) -> ParsedMedia:
    path = Path(relative_path)
    searchable = str(path)
    filename = path.name

    for parser_name, pattern, confidence in TV_PATTERNS:
        match = pattern.search(searchable)

        if match:
            return ParsedMedia(
                media_type="tv",
                show=_show_from_path(path, match.group("show")),
                season=int(match.group("season")),
                episode=int(match.group("episode")),
                confidence=confidence,
                parser=parser_name,
            )

    special = SPECIAL_PATTERN.search(searchable)

    if special:
        title = clean_title_case(
            SPECIAL_PATTERN.sub(" ", Path(filename).stem)
        )

        return ParsedMedia(
            media_type="special",
            title=title or None,
            show=_show_from_path(path, None),
            season=int(special.group("season")),
            episode=int(special.group("special")),
            confidence=82,
            parser="season-movie-special",
            reason="Special or television movie pattern requires review",
        )

    parent = path.parent.name
    season_match = SEASON_FOLDER.match(parent)
    episode_match = EPISODE_ONLY.search(Path(filename).stem)

    if season_match and episode_match:
        show = None

        if len(path.parts) >= 3:
            show = clean_title_case(path.parts[-3])

        return ParsedMedia(
            media_type="tv",
            show=show,
            season=int(season_match.group("season")),
            episode=int(episode_match.group("episode")),
            confidence=92,
            parser="season-folder-episode-file",
        )

    if season_match:
        show = None

        if len(path.parts) >= 3:
            show = clean_title_case(path.parts[-3])

        return ParsedMedia(
            media_type="tv_review",
            show=show,
            season=int(season_match.group("season")),
            confidence=55,
            parser="season-folder",
            reason="Season detected but no reliable episode number was found",
        )

    year_matches = list(YEAR_PATTERN.finditer(searchable))

    if year_matches:
        year_match = year_matches[-1]
        year = int(year_match.group("year"))

        file_stem = Path(filename).stem
        filename_years = list(YEAR_PATTERN.finditer(file_stem))

        if filename_years:
            title_source = file_stem[: filename_years[-1].start()]
        else:
            title_source = path.parent.name

        title = clean_title_case(title_source)

        return ParsedMedia(
            media_type="movie",
            title=title or clean_title_case(path.parent.name),
            year=year,
            confidence=88,
            parser="movie-year",
        )

    cleaned_filename = clean_release_name(filename)
    cleaned_parent = clean_release_name(path.parent.name)

    if (
        cleaned_filename
        and cleaned_parent
        and cleaned_filename.casefold() == cleaned_parent.casefold()
    ):
        return ParsedMedia(
            media_type="movie_review",
            title=clean_title_case(cleaned_parent),
            confidence=65,
            parser="matching-folder-filename",
            reason="Folder and filename match but no release year was detected",
        )

    return ParsedMedia(
        media_type="unknown",
        title=clean_title_case(path.parent.name) or None,
        confidence=0,
        parser="unknown",
        reason="No reliable movie or television pattern was detected",
    )
