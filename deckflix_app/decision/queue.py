from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from deckflix_app.library import LibraryIndex
from deckflix_app.library.index import media_key
from deckflix_app.media import MediaInfo
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.probe import probe_media
from deckflix_app.quality import quality_score
from deckflix_app.scanner import metadata_from_file, scan_videos

from .actions import Action
from .engine import decide, decide_with_technical
from .models import Decision


@dataclass(slots=True)
class DecisionQueueItem:
    incoming: MediaMetadata
    existing: MediaMetadata | None
    decision: Decision


@dataclass(slots=True)
class DecisionQueue:
    items: list[DecisionQueueItem]

    @property
    def total(self) -> int:
        return len(self.items)

    def count(self, action: Action) -> int:
        return sum(
            1
            for item in self.items
            if item.decision.action is action
        )

    def summary(self) -> dict[Action, int]:
        counts = Counter(
            item.decision.action
            for item in self.items
        )

        return {
            action: counts.get(action, 0)
            for action in Action
        }


def metadata_from_media_info(
    media: MediaInfo,
) -> MediaMetadata:
    size = 0

    try:
        size = media.path.stat().st_size
    except OSError:
        pass

    return MediaMetadata(
        media_type=media.media_type,
        title=media.title,
        content_type=(
            "episode"
            if media.media_type == "tv"
            else "movie"
        ),
        year=media.year,
        season=media.season,
        episode=media.episode,
        resolution=(
            None
            if media.resolution == "unknown"
            else media.resolution
        ),
        source=(
            None
            if media.source == "unknown"
            else media.source
        ),
        video_codec=(
            None
            if media.codec == "unknown"
            else media.codec
        ),
        container=media.path.suffix.lstrip(".").lower(),
        path=media.path,
        size=size,
    )


def scan_metadata(
    path: Path,
) -> list[MediaMetadata]:
    """
    Scan a media root using DeckFlix's canonical metadata parser.

    metadata_from_file() is deliberately used here rather than
    rebuilding metadata from inspect_media(). This keeps the
    decision queue aligned with the scanner's canonical handling
    of contextual TV media, Extras, special episodes, and movie
    filename parsing.
    """
    return [
        metadata_from_file(file)
        for file in scan_videos(path)
    ]


def _deduplicate_incoming(
    incoming: list[MediaMetadata],
) -> list[MediaMetadata]:
    """
    Collapse multiple shuttle files representing the same logical
    media item into one candidate.

    The logical identity is the same identity used by LibraryIndex:
      - TV: title + season + episode
      - Movies: title + year

    When multiple incoming files have the same logical identity,
    retain the highest-quality candidate.

    Equal-quality candidates retain the first occurrence. This keeps
    the result deterministic with respect to the scanner's ordering
    and avoids inventing a preference between equivalent releases.

    This remains filename-metadata based. Operational technical
    verification is applied after this selection and does not alter
    incoming deduplication behaviour.

    No filesystem changes are performed.
    """
    selected: dict[
        tuple,
        MediaMetadata,
    ] = {}

    for media in incoming:
        key = media_key(media)
        current = selected.get(key)

        if current is None:
            selected[key] = media
            continue

        incoming_score = quality_score(media)
        current_score = quality_score(current)

        if incoming_score > current_score:
            selected[key] = media

    return list(selected.values())


def build_decision_queue(
    *,
    incoming: list[MediaMetadata],
    library: list[MediaMetadata],
) -> DecisionQueue:
    """
    Build a decision queue from already-parsed metadata.

    This path is deliberately pure with respect to technical probing.
    It is used by deterministic analysis and tests and preserves the
    existing filename-derived decision behaviour.
    """
    index = LibraryIndex()

    for media in library:
        index.add(media)

    deduplicated_incoming = _deduplicate_incoming(
        incoming
    )

    items = []

    for media in deduplicated_incoming:
        existing = index.find(media)

        items.append(
            DecisionQueueItem(
                incoming=media,
                existing=existing,
                decision=decide(existing, media),
            )
        )

    return DecisionQueue(items=items)


def _build_verified_decision_queue(
    *,
    incoming: list[MediaMetadata],
    library: list[MediaMetadata],
) -> DecisionQueue:
    """
    Build the operational decision queue using technical metadata
    from the real files when paths are available.

    ffprobe is read-only. Failed or unavailable probes are passed to
    decide_with_technical(), whose enrichment seam preserves the
    filename-derived decision when verified technical data cannot be
    obtained.

    Incoming deduplication intentionally remains filename-based.
    """
    index = LibraryIndex()

    for media in library:
        index.add(media)

    deduplicated_incoming = _deduplicate_incoming(
        incoming
    )

    items = []

    for media in deduplicated_incoming:
        existing = index.find(media)

        incoming_technical = None
        existing_technical = None

        if media.path is not None:
            incoming_technical = probe_media(
                media.path
            )

        if (
            existing is not None
            and existing.path is not None
        ):
            existing_technical = probe_media(
                existing.path
            )

        decision = decide_with_technical(
            existing,
            media,
            existing_technical=existing_technical,
            incoming_technical=incoming_technical,
        )

        items.append(
            DecisionQueueItem(
                incoming=media,
                existing=existing,
                decision=decision,
            )
        )

    return DecisionQueue(items=items)


def build_decision_queue_from_paths(
    *,
    shuttle_path: Path,
    movie_libraries: list[Path],
    tv_libraries: list[Path],
) -> DecisionQueue:
    """
    Build the operational queue from real filesystem roots.

    Real-path queue construction owns technical probing. The pure
    build_decision_queue() API remains probe-free.
    """
    incoming = scan_metadata(shuttle_path)

    library = []

    for path in [*movie_libraries, *tv_libraries]:
        library.extend(
            scan_metadata(path)
        )

    return _build_verified_decision_queue(
        incoming=incoming,
        library=library,
    )
