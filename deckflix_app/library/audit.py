from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re

from deckflix_app.library.index import (
    MediaKey,
    media_key,
)
from deckflix_app.metadata.models import (
    MediaMetadata,
)
from deckflix_app.scanner import scan_media


class LibraryIssue(str, Enum):
    MISPLACED = "MISPLACED"
    LEGACY_LOCATION = "LEGACY_LOCATION"
    DUPLICATE_CANDIDATE = "DUPLICATE_CANDIDATE"
    STRUCTURE_REVIEW = "STRUCTURE_REVIEW"
    WEAK_METADATA = "WEAK_METADATA"


class DuplicateClassification(str, Enum):
    LEGACY_DUPLICATE = "LEGACY_DUPLICATE"
    LIKELY_EXACT_DUPLICATE = "LIKELY_EXACT_DUPLICATE"
    BETTER_QUALITY = "BETTER_QUALITY"
    QUALITY_VARIANT = "QUALITY_VARIANT"
    POSSIBLE_FALSE_POSITIVE = "POSSIBLE_FALSE_POSITIVE"


@dataclass(frozen=True, slots=True)
class LibraryRoot:
    name: str
    path: Path
    expected_media_type: str
    primary: bool


@dataclass(slots=True)
class LibraryAuditEntry:
    root: LibraryRoot
    media: MediaMetadata
    relative_path: Path
    issues: set[LibraryIssue]

    @property
    def path(self) -> Path:
        if self.media.path is None:
            return self.root.path / self.relative_path

        return self.media.path

    @property
    def ok(self) -> bool:
        return not self.issues


@dataclass(frozen=True, slots=True)
class LibraryAuditSummary:
    total_videos: int
    movie_videos: int
    tv_videos: int
    correct: int
    misplaced: int
    legacy: int
    duplicate_candidates: int
    structure_review: int
    weak_metadata: int
    total_bytes: int


@dataclass(slots=True)
class LibraryAudit:
    entries: list[LibraryAuditEntry]

    duplicate_groups: dict[
        MediaKey,
        tuple[LibraryAuditEntry, ...],
    ]

    duplicate_classifications: dict[
        MediaKey,
        DuplicateClassification,
    ] = field(default_factory=dict)

    @property
    def summary(self) -> LibraryAuditSummary:
        total_bytes = sum(
            entry.media.size
            for entry in self.entries
        )

        return LibraryAuditSummary(
            total_videos=len(self.entries),
            movie_videos=sum(
                1
                for entry in self.entries
                if entry.media.media_type == "movie"
            ),
            tv_videos=sum(
                1
                for entry in self.entries
                if entry.media.media_type == "tv"
            ),
            correct=sum(
                1
                for entry in self.entries
                if entry.ok
            ),
            misplaced=sum(
                1
                for entry in self.entries
                if LibraryIssue.MISPLACED in entry.issues
            ),
            legacy=sum(
                1
                for entry in self.entries
                if LibraryIssue.LEGACY_LOCATION in entry.issues
            ),
            duplicate_candidates=sum(
                1
                for entry in self.entries
                if LibraryIssue.DUPLICATE_CANDIDATE
                in entry.issues
            ),
            structure_review=sum(
                1
                for entry in self.entries
                if LibraryIssue.STRUCTURE_REVIEW
                in entry.issues
            ),
            weak_metadata=sum(
                1
                for entry in self.entries
                if LibraryIssue.WEAK_METADATA
                in entry.issues
            ),
            total_bytes=total_bytes,
        )


def _metadata_is_weak(
    media: MediaMetadata,
) -> bool:
    if not media.title.strip():
        return True

    if media.media_type == "tv":
        if media.content_type == "episode":
            return (
                media.season is None
                or media.episode is None
            )

        return False

    if media.media_type == "movie":
        return media.year is None

    return True


def _is_tv_associated_special(
    root: LibraryRoot,
    media: MediaMetadata,
    relative_path: Path,
) -> bool:
    if root.expected_media_type != "tv":
        return False

    parts = [
        part.casefold()
        for part in relative_path.parts
    ]

    stem = relative_path.stem.casefold()

    if "extras" in parts:
        return True

    if any(
        "special" in part
        or "featurette" in part
        or "bonus" in part
        for part in parts
    ):
        return True

    if re.search(
        r"\bs\d{1,2}x\d{1,3}\b",
        stem,
        re.IGNORECASE,
    ):
        return True

    if media.title.casefold().endswith(" extras"):
        return True

    if media.title.casefold().endswith(" special"):
        return True

    return False


def _is_collection_structure(
    relative_path: Path,
) -> bool:
    if len(relative_path.parts) < 3:
        return False

    ancestors = [
        part.casefold()
        for part in relative_path.parts[:-1]
    ]

    markers = (
        "collection",
        "trilogy",
        "movies",
        "series",
        "saga",
        "anthology",
    )

    return any(
        marker in ancestor
        for ancestor in ancestors
        for marker in markers
    )


def _needs_structure_review(
    root: LibraryRoot,
    relative_path: Path,
) -> bool:
    depth = len(relative_path.parts)

    if root.expected_media_type == "movie":
        if depth <= 2:
            return False

        if _is_collection_structure(relative_path):
            return False

        return True

    if depth <= 3:
        return False

    parts = [
        part.casefold()
        for part in relative_path.parts[:-1]
    ]

    if "extras" in parts or "specials" in parts:
        return False

    return True


def _entry_for_media(
    root: LibraryRoot,
    media: MediaMetadata,
) -> LibraryAuditEntry:
    if media.path is None:
        raise ValueError(
            "Scanned media has no filesystem path"
        )

    relative = media.path.relative_to(root.path)

    issues: set[LibraryIssue] = set()

    effective_media_type = media.media_type

    if _is_tv_associated_special(
        root,
        media,
        relative,
    ):
        effective_media_type = "tv"

    if effective_media_type != root.expected_media_type:
        issues.add(LibraryIssue.MISPLACED)

    if not root.primary:
        issues.add(LibraryIssue.LEGACY_LOCATION)

    if _needs_structure_review(
        root,
        relative,
    ):
        issues.add(LibraryIssue.STRUCTURE_REVIEW)

    if _metadata_is_weak(media):
        issues.add(LibraryIssue.WEAK_METADATA)

    return LibraryAuditEntry(
        root=root,
        media=media,
        relative_path=relative,
        issues=issues,
    )


def _duplicate_key_is_strong(
    key: MediaKey,
) -> bool:
    if key[0] == "movie":
        return key[2] is not None

    if key[0] == "tv":
        return (
            key[2] is not None
            and key[3] is not None
        )

    return False


def _normalise_quality_value(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return value.strip().casefold()


def _resolution_rank(
    value: str | None,
) -> int:
    ranks = {
        "480p": 1,
        "720p": 2,
        "1080p": 3,
        "2160p": 4,
    }

    return ranks.get(
        _normalise_quality_value(value),
        0,
    )


def _source_rank(
    value: str | None,
) -> int:
    ranks = {
        "dvd": 1,
        "web": 2,
        "webrip": 3,
        "web-dl": 4,
        "bluray": 5,
        "remux": 6,
    }

    return ranks.get(
        _normalise_quality_value(value),
        0,
    )


def _codec_rank(
    value: str | None,
) -> int:
    value = _normalise_quality_value(value)

    if value in {
        "hevc",
        "x265",
        "h265",
    }:
        return 2

    if value in {
        "x264",
        "h264",
    }:
        return 1

    return 0


def _quality_score(
    media: MediaMetadata,
) -> tuple[int, int, int]:
    return (
        _resolution_rank(media.resolution),
        _source_rank(media.source),
        _codec_rank(media.video_codec),
    )


def _quality_signature(
    media: MediaMetadata,
) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
]:
    return (
        _normalise_quality_value(media.resolution),
        _normalise_quality_value(media.source),
        _normalise_quality_value(media.video_codec),
        _normalise_quality_value(media.container),
    )


def _is_legacy_entry(
    entry: LibraryAuditEntry,
) -> bool:
    return (
        LibraryIssue.LEGACY_LOCATION
        in entry.issues
    )


def _looks_like_split_part(
    entry: LibraryAuditEntry,
) -> bool:
    """
    Detect common multi-part release naming.

    These should not automatically be treated as
    duplicate episodes/movies merely because the
    parser produced the same canonical identity.
    """
    text = " ".join(
        (
            entry.relative_path.stem,
            entry.media.title,
        )
    ).casefold()

    patterns = (
        r"\bpart[ ._-]*[12]\b",
        r"\bpart[ ._-]*[0-9]+\b",
        r"\bcd[ ._-]*[12]\b",
        r"\bdisc[ ._-]*[12]\b",
        r"\bdisk[ ._-]*[12]\b",
        r"\bsegment[ ._-]*[12]\b",
        r"\bpt[ ._-]*[12]\b",
    )

    return any(
        re.search(pattern, text)
        for pattern in patterns
    )


def _known_quality_difference(
    first: MediaMetadata,
    second: MediaMetadata,
) -> bool:
    """
    Return True only when a quality attribute is
    known on both sides and differs.

    Missing metadata must not be interpreted as
    lower or higher quality.
    """
    pairs = (
        (
            _normalise_quality_value(
                first.resolution
            ),
            _normalise_quality_value(
                second.resolution
            ),
        ),
        (
            _normalise_quality_value(
                first.source
            ),
            _normalise_quality_value(
                second.source
            ),
        ),
        (
            _normalise_quality_value(
                first.video_codec
            ),
            _normalise_quality_value(
                second.video_codec
            ),
        ),
    )

    return any(
        left is not None
        and right is not None
        and left != right
        for left, right in pairs
    )


def _has_meaningful_quality_metadata(
    media: MediaMetadata,
) -> bool:
    return any(
        (
            media.resolution,
            media.source,
            media.video_codec,
        )
    )


def _classify_duplicate_group(
    group: tuple[LibraryAuditEntry, ...],
) -> DuplicateClassification:
    primary = [
        entry
        for entry in group
        if not _is_legacy_entry(entry)
    ]

    legacy = [
        entry
        for entry in group
        if _is_legacy_entry(entry)
    ]

    # Primary + legacy is its own category.
    # It must be evaluated before quality ranking.
    if primary and legacy:
        return (
            DuplicateClassification
            .LEGACY_DUPLICATE
        )

    # Detect likely split files such as
    # "Part 1" / "Part 2" before calling them
    # quality variants.
    if any(
        _looks_like_split_part(entry)
        for entry in group
    ):
        return (
            DuplicateClassification
            .POSSIBLE_FALSE_POSITIVE
        )

    signatures = {
        _quality_signature(entry.media)
        for entry in group
    }

    sizes = {
        entry.media.size
        for entry in group
    }

    if len(signatures) == 1 and len(sizes) == 1:
        return (
            DuplicateClassification
            .LIKELY_EXACT_DUPLICATE
        )

    # If every entry has exactly the same known
    # quality information but sizes differ, we
    # cannot safely call one a better release.
    if len(
        {
            _quality_signature(entry.media)
            for entry in group
        }
    ) == 1:
        return (
            DuplicateClassification
            .QUALITY_VARIANT
        )

    quality_entries = [
        entry
        for entry in group
        if _has_meaningful_quality_metadata(
            entry.media
        )
    ]

    if len(quality_entries) >= 2:
        scores = [
            _quality_score(entry.media)
            for entry in quality_entries
        ]

        best = max(scores)

        if scores.count(best) == 1:
            best_entry = quality_entries[
                scores.index(best)
            ]

            other_entries = [
                entry
                for entry in quality_entries
                if entry is not best_entry
            ]

            if any(
                _known_quality_difference(
                    best_entry.media,
                    other.media,
                )
                for other in other_entries
            ):
                return (
                    DuplicateClassification
                    .BETTER_QUALITY
                )

    # Same identity with materially different
    # file sizes but little usable metadata is still
    # a variant, not automatically a false positive.
    return (
        DuplicateClassification
        .QUALITY_VARIANT
    )


def audit_libraries(
    roots: list[LibraryRoot],
) -> LibraryAudit:
    """
    Read-only audit of existing media roots.

    No files are renamed, moved, copied, deleted,
    modified, or submitted to Jellyfin.
    """
    entries: list[LibraryAuditEntry] = []

    for root in roots:
        root_path = Path(root.path).resolve()

        normalized_root = LibraryRoot(
            name=root.name,
            path=root_path,
            expected_media_type=root.expected_media_type,
            primary=root.primary,
        )

        for media in scan_media(root_path):
            entries.append(
                _entry_for_media(
                    normalized_root,
                    media,
                )
            )

    groups: dict[
        MediaKey,
        list[LibraryAuditEntry],
    ] = defaultdict(list)

    for entry in entries:
        key = media_key(entry.media)

        if not _duplicate_key_is_strong(key):
            continue

        groups[key].append(entry)

    duplicate_groups: dict[
        MediaKey,
        tuple[LibraryAuditEntry, ...],
    ] = {}

    duplicate_classifications: dict[
        MediaKey,
        DuplicateClassification,
    ] = {}

    for key, group in groups.items():
        if len(group) <= 1:
            continue

        duplicate_group = tuple(group)

        duplicate_groups[key] = duplicate_group

        duplicate_classifications[key] = (
            _classify_duplicate_group(
                duplicate_group
            )
        )

        for entry in group:
            entry.issues.add(
                LibraryIssue.DUPLICATE_CANDIDATE
            )

    return LibraryAudit(
        entries=entries,
        duplicate_groups=duplicate_groups,
        duplicate_classifications=(
            duplicate_classifications
        ),
    )


def current_deckflix_library_roots(
) -> list[LibraryRoot]:
    """
    Current migration topology.

    library1/movie and library2/tv are intended
    final locations.

    library1/tv and library2/movie are existing
    legacy collections to be reconciled.
    """
    return [
        LibraryRoot(
            name="Primary Movies",
            path=Path("/data/library1/movie"),
            expected_media_type="movie",
            primary=True,
        ),
        LibraryRoot(
            name="Legacy TV",
            path=Path("/data/library1/tv"),
            expected_media_type="tv",
            primary=False,
        ),
        LibraryRoot(
            name="Legacy Movies",
            path=Path("/data/library2/movie"),
            expected_media_type="movie",
            primary=False,
        ),
        LibraryRoot(
            name="Primary TV",
            path=Path("/data/library2/tv"),
            expected_media_type="tv",
            primary=True,
        ),
    ]
