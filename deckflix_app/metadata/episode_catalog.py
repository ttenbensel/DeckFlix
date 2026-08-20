from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata


@dataclass(frozen=True, slots=True)
class EpisodeIdentity:
    title: str
    season: int
    episode: int


_SEASON_DIRECTORY_PATTERN = re.compile(
    r"""
    ^
    season[ ._-]*0*
    (\d{1,3})
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _normalize_title(value: str) -> str:
    """
    Produce a conservative comparison key.

    Normalization removes capitalization and punctuation
    differences only. It does not perform fuzzy matching.
    """
    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    value = value.casefold()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


_SIMPSONS_SEASON_9 = {
    "The City of New York vs. Homer Simpson": 1,
    "The Principal and the Pauper": 2,
    "Lisa's Sax": 3,
    "Treehouse of Horror VIII": 4,
    "The Cartridge Family": 5,
    "Bart Star": 6,
    "The Two Mrs. Nahasapeemapetilons": 7,
    "Lisa the Skeptic": 8,
    "Realty Bites": 9,
    "Miracle on Evergreen Terrace": 10,
    "All Singing, All Dancing": 11,
    "Bart Carny": 12,
    "The Joy of Sect": 13,
    "Das Bus": 14,
    "The Last Temptation of Krust": 15,
    "Dumbbell Indemnity": 16,
    "Lisa the Simpson": 17,
    "This Little Wiggy": 18,
    "Simpson Tide": 19,
    "The Trouble with Trillions": 20,
    "Girly Edition": 21,
    "Trash of the Titans": 22,
    "King of the Hill": 23,
    "Lost Our Lisa": 24,
    "Natural Born Kissers": 25,
}


_CATALOGS = {
    (
        _normalize_title(
            "The Simpsons"
        ),
        9,
    ): {
        _normalize_title(title): episode
        for title, episode
        in _SIMPSONS_SEASON_9.items()
    },
}


_ALIASES = {
    (
        _normalize_title(
            "The Simpsons"
        ),
        9,
        _normalize_title(
            "Dumbell Indemnity"
        ),
    ): 16,
}


def _season_context(
    path: Path,
) -> tuple[str, int] | None:
    """
    Return (series title, season) only when the file is
    beneath an explicit Season directory.

    Example:

        The Simpsons/
            Season 9/
                Bart Carny.m4v

        -> ("The Simpsons", 9)
    """
    for parent in path.parents:
        match = (
            _SEASON_DIRECTORY_PATTERN
            .fullmatch(
                parent.name
            )
        )

        if match is None:
            continue

        season = int(
            match.group(1)
        )

        show_directory = parent.parent

        if show_directory == parent:
            return None

        show_title = (
            show_directory.name.strip()
        )

        if not show_title:
            return None

        return show_title, season

    return None


def resolve_title_only_episode(
    path: str | Path,
    *,
    candidate_title: str | None = None,
) -> EpisodeIdentity | None:
    """
    Resolve a title-only TV episode from a trusted catalogue.

    This deliberately fails closed.

    Requirements:
      - explicit Season directory;
      - known series + season catalogue;
      - exact normalized title or explicit alias.

    Directory order, filename order, fuzzy similarity, and
    partial-title matching are never used.
    """
    path = Path(path)

    context = _season_context(
        path
    )

    if context is None:
        return None

    show_title, season = context

    show_key = _normalize_title(
        show_title
    )

    catalog = _CATALOGS.get(
        (
            show_key,
            season,
        )
    )

    if catalog is None:
        return None

    title = (
        candidate_title
        if candidate_title is not None
        else path.stem
    )

    title_key = _normalize_title(
        title
    )

    episode = catalog.get(
        title_key
    )

    if episode is None:
        episode = _ALIASES.get(
            (
                show_key,
                season,
                title_key,
            )
        )

    if episode is None:
        return None

    return EpisodeIdentity(
        title=show_title,
        season=season,
        episode=episode,
    )
