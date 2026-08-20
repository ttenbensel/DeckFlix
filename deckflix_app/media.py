from dataclasses import dataclass
from pathlib import Path
import re


VIDEO_EXTENSIONS = {
    ".avi",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".wmv",
}


@dataclass
class MediaInfo:
    path: Path
    media_type: str
    title: str
    year: int | None
    season: int | None
    episode: int | None
    resolution: str
    source: str
    codec: str
    quality_score: int

    @property
    def key(self):
        if (
            self.media_type == "tv"
            and self.season is not None
            and self.episode is not None
        ):
            return (
                f"{self.title.lower()} "
                f"s{self.season:02d}e{self.episode:02d}"
            )

        if self.year:
            return f"{self.title.lower()} {self.year}"

        return self.title.lower()


TV_EPISODE_PATTERNS = [
    # Show.S01E02
    re.compile(
        r"[Ss]\s*(\d{1,2})\s*[Ee]\s*(\d{1,3})",
        re.IGNORECASE,
    ),

    # Show.1x02
    #
    # Reject codec-like tokens such as:
    #     1 X 264
    #     1 X 265
    #     1 X 266
    #
    # These commonly appear in release names and are
    # not season/episode identities.
    re.compile(
        r"\b(\d{1,2})\s*[Xx]\s*(?!26[456]\b)(\d{1,3})\b",
        re.IGNORECASE,
    ),

    # Show [1.02]
    #
    # Episode component must contain at least two
    # digits. This prevents common surround-audio
    # tags such as [5.1] and [7.1] being interpreted
    # as S05E01 / S07E01.
    re.compile(
        r"\[(\d{1,2})\.(\d{2,3})\]",
        re.IGNORECASE,
    ),

    # Show 01E02
    re.compile(
        r"\b(\d{1,2})\s*[Ee]\s*(\d{1,3})\b",
        re.IGNORECASE,
    ),

    # Season 1 Episode 2
    re.compile(
        r"""
        [Ss]eason[ ._-]*(\d{1,2})
        [ ._-]*
        [Ee]pisode[ ._-]*
        (\d{1,3})
        """,
        re.IGNORECASE | re.VERBOSE,
    ),

    # Series 1 2of6
    re.compile(
        r"""
        [Ss]eries[ ._-]*(\d{1,2})
        [ ._-]*
        (\d{1,3})
        \s*of\s*\d+
        """,
        re.IGNORECASE | re.VERBOSE,
    ),
]


SPECIAL_X_PATTERN = re.compile(
    r"""
    [Ss]\s*(\d{1,2})
    \s*[Xx]\s*
    (\d{1,3})
    """,
    re.IGNORECASE | re.VERBOSE,
)


SEASON_DIRECTORY_PATTERN = re.compile(
    r"""
    ^
    (?:complete[ ._-]*)?
    season[ ._-]*
    (\d{1,2})
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)


TV_MARKER_PATTERN = re.compile(
    r"""
    (?:
        [Ss]\s*\d{1,2}\s*[Ee]\s*\d{1,3}
        |
        \b\d{1,2}\s*[Xx]\s*\d{1,3}\b
        |
        \[\d{1,2}\.\d{1,3}\]
        |
        \b\d{1,2}\s*[Ee]\s*\d{1,3}\b
        |
        [Ss]eason[ ._-]*\d{1,2}
        [ ._-]*
        [Ee]pisode[ ._-]*
        \d{1,3}
        |
        [Ss]eries[ ._-]*\d{1,2}
        [ ._-]*
        \d{1,3}
        \s*of\s*\d+
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


PART_PATTERN = re.compile(
    r"\bpart[ ._-]*(\d{1,3})\b",
    re.IGNORECASE,
)


EPISODE_WORD_PATTERN = re.compile(
    r"\bepisode[ ._-]*(\d{1,3})\b",
    re.IGNORECASE,
)


HASH_EPISODE_PATTERN = re.compile(
    r"""
    (?:^|[ ._-])
    \#\s*
    (\d{1,3})
    (?=[ ._-]|$)
    """,
    re.IGNORECASE | re.VERBOSE,
)


BARE_E_PATTERN = re.compile(
    r"\b[Ee](\d{1,3})\b",
)


PARENT_SEASON_PATTERN = re.compile(
    r"\b[Ss](\d{1,2})\b",
)


GENERIC_DIRECTORIES = {
    "",
    "extras",
    "extra",
    "featurettes",
    "featurette",
    "sample",
    "samples",
    "season",
    "tv",
    "television",
    "media",
    "shuttle",
}


def detect_year(text):
    match = re.search(
        r"\b(19|20)\d{2}\b",
        str(text),
    )

    if not match:
        return None

    try:
        return int(match.group(0))
    except Exception:
        return None


def detect_tv_episode(text):
    text = str(text)

    # SxxXyy is deliberately excluded.
    #
    # Real-world DeckFlix data showed X notation may
    # represent specials rather than the ordinary
    # E-numbered episode at the same season/number.
    if SPECIAL_X_PATTERN.search(text):
        return None, None

    for pattern in TV_EPISODE_PATTERNS:
        match = pattern.search(text)

        if not match:
            continue

        try:
            season = int(match.group(1))
            episode = int(match.group(2))
        except (TypeError, ValueError):
            continue

        if season < 0:
            continue

        if episode <= 0:
            continue

        if episode in {
            360,
            480,
            576,
            720,
        }:
            continue

        return season, episode

    return None, None


def detect_resolution(text):
    lower = str(text).lower()

    if "2160p" in lower or "4k" in lower:
        return "2160p"

    if "1080p" in lower:
        return "1080p"

    if "720p" in lower:
        return "720p"

    if "480p" in lower:
        return "480p"

    if "360p" in lower:
        return "360p"

    return "unknown"


def detect_source(text):
    lower = str(text).lower()

    if (
        "bluray" in lower
        or "blu-ray" in lower
        or "brrip" in lower
    ):
        return "BluRay"

    if (
        "web-dl" in lower
        or "webdl" in lower
    ):
        return "WEB-DL"

    if "webrip" in lower:
        return "WEBRip"

    if "hdtv" in lower:
        return "HDTV"

    if "hdrip" in lower:
        return "HDRip"

    if (
        "dvdscr" in lower
        or "screener" in lower
    ):
        return "Screener"

    return "unknown"


def detect_codec(text):
    lower = str(text).lower()

    if (
        "x265" in lower
        or "h265" in lower
        or "hevc" in lower
    ):
        return "HEVC"

    if (
        "x264" in lower
        or "h264" in lower
    ):
        return "H264"

    return "unknown"


def clean_title(text):
    name = str(text)

    name = re.sub(
        r"\[[^\]]*\]",
        " ",
        name,
    )

    name = re.sub(
        r"\([^\)]*\)",
        " ",
        name,
    )

    name = re.sub(
        r"\b(19|20)\d{2}\b",
        " ",
        name,
    )

    remove_terms = [
        "2160p",
        "1080p",
        "720p",
        "480p",
        "360p",
        "4k",
        "webrip",
        "web-dl",
        "webdl",
        "bluray",
        "blu-ray",
        "brrip",
        "hdtv",
        "hdrip",
        "dvdscr",
        "screener",
        "x264",
        "x265",
        "h264",
        "h265",
        "hevc",
        "aac",
        "ddp",
        "dd5",
        "5.1",
        "10bit",
        "yts",
        "tgx",
        "rarbg",
        "galaxyrg",
        "repack",
        "proper",
        "imax",
    ]

    for term in remove_terms:
        name = re.sub(
            rf"\b{re.escape(term)}\b",
            " ",
            name,
            flags=re.IGNORECASE,
        )

    name = re.sub(
        r"[._-]+",
        " ",
        name,
    )

    name = re.sub(
        r"[^a-zA-Z0-9 ]+",
        " ",
        name,
    )

    name = " ".join(
        name.split()
    )

    return name.strip()


def score_quality(path):
    text = str(path).lower()
    score = 0

    resolution = detect_resolution(text)
    source = detect_source(text)
    codec = detect_codec(text)

    if resolution == "2160p":
        score += 60
    elif resolution == "1080p":
        score += 40
    elif resolution == "720p":
        score += 20
    elif resolution == "480p":
        score += 5
    elif resolution == "360p":
        score += 1

    if source == "BluRay":
        score += 25
    elif source == "WEB-DL":
        score += 20
    elif source == "WEBRip":
        score += 15
    elif source == "HDTV":
        score += 10
    elif source == "HDRip":
        score += 5
    elif source == "Screener":
        score -= 20

    if codec == "HEVC":
        score += 5

    if (
        "repack" in text
        or "proper" in text
    ):
        score += 5

    if "sample" in text:
        score -= 50

    if "copy" in text:
        score -= 30

    try:
        score += min(
            int(
                Path(path).stat().st_size
                / 1024**3
            ),
            20,
        )
    except Exception:
        pass

    return score


def _season_directory_context(
    path: Path,
) -> tuple[int | None, str | None]:
    for parent in path.parents:
        match = SEASON_DIRECTORY_PATTERN.fullmatch(
            parent.name
        )

        if not match:
            continue

        season = int(match.group(1))
        show_directory = parent.parent

        if show_directory == parent:
            return season, None

        title = clean_title(
            show_directory.name
        )

        if not title:
            title = None

        return season, title

    return None, None


def _scene_episode_for_season(
    stem: str,
    season: int,
) -> int | None:
    for match in re.finditer(
        r"""
        (?:^|[._ -])
        (\d{3,4})
        (?=[._ -]|$)
        """,
        stem,
        re.VERBOSE,
    ):
        token = match.group(1)

        try:
            token_season = int(
                token[:-2]
            )
            token_episode = int(
                token[-2:]
            )
        except ValueError:
            continue

        if token_season != season:
            continue

        if token_episode <= 0:
            continue

        return token_episode

    return None


def _part_number_in_season_context(
    path: Path,
) -> int | None:
    """
    Treat Part xx as an episode number when the file
    already lives inside an explicit Season directory.

    Require at least three sibling Part files so movie
    titles such as Part One / Part Two are not promoted
    to television merely because they contain "Part".
    """
    match = PART_PATTERN.search(
        path.stem
    )

    if not match:
        return None

    siblings = _video_siblings(
        path
    )

    part_numbers = []

    for sibling in siblings:
        sibling_match = PART_PATTERN.search(
            sibling.stem
        )

        if not sibling_match:
            continue

        part_numbers.append(
            int(
                sibling_match.group(1)
            )
        )

    if len(set(part_numbers)) < 3:
        return None

    episode = int(
        match.group(1)
    )

    if episode <= 0:
        return None

    return episode


def _episode_number_in_season_context(
    stem: str,
) -> int | None:
    """
    Return an explicit episode number when the enclosing
    directory has already established the season.

    Supported contextual forms include:

        Episode 04
        E04
        # 04

    The hash form is deliberately valid only here, after an
    explicit Season directory has supplied the season identity.
    A bare "# 04" elsewhere is not enough evidence to classify
    a file as television.
    """
    match = EPISODE_WORD_PATTERN.search(
        stem
    )

    if match:
        episode = int(match.group(1))

        if episode > 0:
            return episode

    match = BARE_E_PATTERN.search(
        stem
    )

    if match:
        episode = int(match.group(1))

        if episode > 0:
            return episode

    match = HASH_EPISODE_PATTERN.search(
        stem
    )

    if match:
        episode = int(match.group(1))

        if episode > 0:
            return episode

    return None


def _contains_episode_marker(text):
    return bool(
        TV_MARKER_PATTERN.search(
            str(text)
        )
    )


def _clean_tv_title_candidate(text):
    original = str(text).strip()

    if re.fullmatch(
        r"(19|20)\d{2}",
        original,
    ):
        return original

    marker = TV_MARKER_PATTERN.search(
        original
    )

    if marker:
        title = original[:marker.start()]
    else:
        title = original

    title = re.sub(
        r"^\s*\d{1,3}[._-]+(?=[A-Za-z0-9])",
        "",
        title,
    )

    title = re.sub(
        r"""
        \b
        (?:complete[ ._-]*)?
        season[ ._-]*\d{1,2}
        \b
        .*$
        """,
        " ",
        title,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    title = re.sub(
        r"""
        \b
        [Ss]\d{1,2}
        \s*$
        """,
        " ",
        title,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    return clean_title(
        title
    ).strip()


def _tv_title_from_path(path):
    for parent in path.parents:
        if not _contains_episode_marker(
            parent.name
        ):
            continue

        candidate = _clean_tv_title_candidate(
            parent.name
        )

        if (
            candidate
            and candidate.lower()
            not in GENERIC_DIRECTORIES
        ):
            return candidate

    if _contains_episode_marker(
        path.stem
    ):
        candidate = _clean_tv_title_candidate(
            path.stem
        )

        if (
            candidate
            and candidate.lower()
            not in GENERIC_DIRECTORIES
        ):
            return candidate

    for parent in path.parents:
        candidate = _clean_tv_title_candidate(
            parent.name
        )

        if (
            not candidate
            or candidate.lower()
            in GENERIC_DIRECTORIES
        ):
            continue

        if SEASON_DIRECTORY_PATTERN.fullmatch(
            parent.name
        ):
            continue

        return candidate

    return _clean_tv_title_candidate(
        path.stem
    )


def _episode_from_parent_release_folder(
    path: Path,
) -> tuple[int | None, int | None]:
    for parent in path.parents:
        season, episode = detect_tv_episode(
            parent.name
        )

        if (
            season is not None
            and episode is not None
        ):
            return season, episode

    return None, None


def _video_siblings(path: Path) -> list[Path]:
    try:
        return [
            sibling
            for sibling in path.parent.iterdir()
            if (
                sibling.is_file()
                and sibling.suffix.lower()
                in VIDEO_EXTENSIONS
            )
        ]
    except OSError:
        return []


def _series_title_for_extra(path: Path) -> str | None:
    """
    Return a series-specific identity for bonus material.

    Examples:

        Rick and Morty/
            Rick and Morty Season 1 1080p HEVC/
                Extras/
                    Behind The Scenes.mkv

        -> Rick and Morty Extras

    Release/collection directories immediately above
    Extras are ignored so unrelated shows can never
    collapse onto a generic "Extras" media identity.
    """
    parents = list(
        path.parents
    )

    extras_index = None

    for index, parent in enumerate(parents):
        lower = parent.name.casefold()

        if (
            lower == "extras"
            or lower.endswith(" extras")
            or lower == "featurettes"
            or lower == "featurette"
        ):
            extras_index = index
            break

    if extras_index is None:
        return None

    generic_release_names = {
        "release",
        "releases",
        "collection",
        "complete",
        "disc",
        "disk",
        "bonus",
        "bonus material",
    }

    release_markers = (
        "season",
        "complete",
        "1080p",
        "720p",
        "480p",
        "360p",
        "2160p",
        "4k",
        "bluray",
        "blu ray",
        "bdrip",
        "brrip",
        "webrip",
        "web dl",
        "webdl",
        "hdtv",
        "x264",
        "x265",
        "h264",
        "h265",
        "hevc",
        "dvdrip",
    )

    for parent in parents[
        extras_index + 1:
        extras_index + 7
    ]:
        raw_name = parent.name
        candidate = clean_title(
            raw_name
        )

        if not candidate:
            continue

        lower_candidate = (
            candidate.casefold()
        )

        lower_raw = (
            raw_name.casefold()
        )

        if (
            lower_candidate
            in GENERIC_DIRECTORIES
        ):
            continue

        if (
            lower_candidate
            in generic_release_names
        ):
            continue

        # Skip release/package directories such as:
        #
        # Rick and Morty Season 1 1080p HEVC
        #
        # so the next ancestor "Rick and Morty"
        # becomes authoritative.
        if any(
            marker in lower_raw
            for marker in release_markers
        ):
            continue

        # Test/runtime/container directories are not
        # meaningful series identities. A real show
        # folder should occur before these.
        if re.fullmatch(
            r"(?:pytest|test)[-_ ]*\\d+",
            lower_candidate,
        ):
            continue

        return (
            f"{candidate} Extras"
        )

    return None


def _looks_like_extra(path: Path) -> bool:
    for parent in path.parents:
        lower = parent.name.casefold()

        if (
            lower == "extras"
            or lower.endswith(" extras")
            or lower == "featurettes"
            or lower == "featurette"
        ):
            return True

    lower_stem = path.stem.casefold()

    return any(
        marker in lower_stem
        for marker in (
            "extra",
            "minisode",
            "behind the scenes",
            "deleted scene",
            "featurette",
            "bloopers",
            "gag reel",
        )
    )


def _legacy_part_episode(
    path: Path,
) -> tuple[str, int, int] | None:
    match = PART_PATTERN.search(
        path.stem
    )

    if not match:
        return None

    siblings = _video_siblings(
        path
    )

    part_numbers = []

    for sibling in siblings:
        sibling_match = PART_PATTERN.search(
            sibling.stem
        )

        if not sibling_match:
            continue

        part_numbers.append(
            int(
                sibling_match.group(1)
            )
        )

    if len(set(part_numbers)) < 3:
        return None

    parent_title = clean_title(
        path.parent.name
    )

    if (
        not parent_title
        or parent_title.casefold()
        in GENERIC_DIRECTORIES
    ):
        return None

    stem_title = clean_title(
        path.stem[
            :match.start()
        ]
    )

    if stem_title:
        parent_key = parent_title.casefold()
        stem_key = stem_title.casefold()

        if (
            not stem_key.startswith(parent_key)
            and not parent_key.startswith(stem_key)
        ):
            return None

    return (
        parent_title,
        1,
        int(match.group(1)),
    )


def _legacy_episode_word(
    path: Path,
) -> tuple[str, int, int] | None:
    if _looks_like_extra(
        path
    ):
        return None

    match = EPISODE_WORD_PATTERN.search(
        path.stem
    )

    if not match:
        return None

    siblings = _video_siblings(
        path
    )

    sibling_episode_count = sum(
        1
        for sibling in siblings
        if EPISODE_WORD_PATTERN.search(
            sibling.stem
        )
    )

    if sibling_episode_count < 3:
        return None

    title_before = clean_title(
        path.stem[
            :match.start()
        ]
    )

    if title_before:
        title = title_before

        title = re.sub(
            r"\bseason\s+\d+\s+prequel\b",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip()

        if not title:
            title = clean_title(
                path.parent.name
            )
    else:
        title = clean_title(
            path.parent.name
        )

    if (
        not title
        or title.casefold()
        in GENERIC_DIRECTORIES
    ):
        return None

    return (
        title,
        1,
        int(match.group(1)),
    )


def _parent_s00_episode(
    path: Path,
) -> tuple[str, int, int] | None:
    episode_match = BARE_E_PATTERN.search(
        path.stem
    )

    if not episode_match:
        return None

    for parent in path.parents:
        season_match = PARENT_SEASON_PATTERN.search(
            parent.name
        )

        if not season_match:
            continue

        season = int(
            season_match.group(1)
        )

        if season != 0:
            continue

        parent_title = re.sub(
            r"\b[Ss]00\b.*$",
            "",
            parent.name,
        )

        title = clean_title(
            parent_title
        )

        if not title:
            continue

        return (
            title,
            0,
            int(
                episode_match.group(1)
            ),
        )

    return None


def inspect_media(path):
    path = Path(
        path
    )

    full_text = str(
        path
    )

    resolution = detect_resolution(
        full_text
    )

    source = detect_source(
        full_text
    )

    codec = detect_codec(
        full_text
    )

    year = detect_year(
        full_text
    )

    # Extras must retain parent-series identity.
    #
    # They remain movie-like/unresolved content for
    # now, so the conservative approval gate keeps
    # them in REVIEW, but "Rick and Morty Extras" can
    # no longer collide with "Spartacus Extras".
    if _looks_like_extra(
        path
    ):
        extra_title = _series_title_for_extra(
            path
        )

        if extra_title:
            return MediaInfo(
                path=path,
                media_type="movie",
                title=extra_title,
                year=None,
                season=None,
                episode=None,
                resolution=resolution,
                source=source,
                codec=codec,
                quality_score=score_quality(
                    path
                ),
            )

    canonical_season, canonical_title = (
        _season_directory_context(
            path
        )
    )

    season, episode = detect_tv_episode(
        path.stem
    )

    if canonical_season is not None:
        if (
            season is None
            or episode is None
        ):
            scene_episode = (
                _scene_episode_for_season(
                    path.stem,
                    canonical_season,
                )
            )

            if scene_episode is not None:
                season = canonical_season
                episode = scene_episode

        if (
            season is None
            or episode is None
        ):
            contextual_episode = (
                _episode_number_in_season_context(
                    path.stem
                )
            )

            if contextual_episode is not None:
                season = canonical_season
                episode = contextual_episode

        if (
            season is None
            or episode is None
        ):
            part_episode = (
                _part_number_in_season_context(
                    path
                )
            )

            if part_episode is not None:
                season = canonical_season
                episode = part_episode

        if (
            season is not None
            and episode is not None
        ):
            return MediaInfo(
                path=path,
                media_type="tv",
                title=(
                    canonical_title
                    or _tv_title_from_path(
                        path
                    )
                ),
                year=None,
                season=season,
                episode=episode,
                resolution=resolution,
                source=source,
                codec=codec,
                quality_score=score_quality(
                    path
                ),
            )

    if (
        season is None
        or episode is None
    ):
        season, episode = (
            _episode_from_parent_release_folder(
                path
            )
        )

    if (
        season is not None
        and episode is not None
    ):
        return MediaInfo(
            path=path,
            media_type="tv",
            title=_tv_title_from_path(
                path
            ),
            year=None,
            season=season,
            episode=episode,
            resolution=resolution,
            source=source,
            codec=codec,
            quality_score=score_quality(
                path
            ),
        )

    legacy = _parent_s00_episode(
        path
    )

    if legacy is None:
        legacy = _legacy_part_episode(
            path
        )

    if legacy is None:
        legacy = _legacy_episode_word(
            path
        )

    if legacy is not None:
        title, season, episode = legacy

        return MediaInfo(
            path=path,
            media_type="tv",
            title=title,
            year=None,
            season=season,
            episode=episode,
            resolution=resolution,
            source=source,
            codec=codec,
            quality_score=score_quality(
                path
            ),
        )

    # SxxXyy is treated as special/unresolved content,
    # not as the ordinary Exx episode.
    special_match = SPECIAL_X_PATTERN.search(
        path.stem
    )

    if special_match:
        title = clean_title(
            path.stem[
                :special_match.start()
            ]
        )

        if not title:
            title = clean_title(
                path.parent.name
            )

        return MediaInfo(
            path=path,
            media_type="movie",
            title=f"{title} Special",
            year=None,
            season=None,
            episode=None,
            resolution=resolution,
            source=source,
            codec=codec,
            quality_score=score_quality(
                path
            ),
        )

    return MediaInfo(
        path=path,
        media_type="movie",
        title=clean_title(
            path.parent.name
        ),
        year=year,
        season=None,
        episode=None,
        resolution=resolution,
        source=source,
        codec=codec,
        quality_score=score_quality(
            path
        ),
    )
