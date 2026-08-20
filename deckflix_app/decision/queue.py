from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from deckflix_app.library import LibraryIndex
from deckflix_app.library.index import media_key
from deckflix_app.media import MediaInfo
from deckflix_app.metadata.enrichment import (
    enrich_quality_from_technical,
)
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

    passthrough: list[MediaMetadata] = []

    for media in incoming:
        # TV content without a complete episode identity cannot be
        # safely deduplicated by title alone.
        #
        # Extras and conservative specials intentionally use
        # season=None / episode=None. Multiple such files from the
        # same series are not necessarily duplicates of each other.
        #
        # Keep those files individually until DeckFlix has a stronger
        # identity than title + unknown season/episode.
        if (
            media.media_type == "tv"
            and (
                media.season is None
                or media.episode is None
            )
        ):
            passthrough.append(media)
            continue

        key = media_key(media)
        current = selected.get(key)

        if current is None:
            selected[key] = media
            continue

        incoming_score = quality_score(media)
        current_score = quality_score(current)

        if incoming_score > current_score:
            selected[key] = media

    return [
        *selected.values(),
        *passthrough,
    ]


def _deduplicate_incoming_verified(
    incoming: list[MediaMetadata],
    *,
    probe_once,
) -> list[MediaMetadata]:
    """
    Operational incoming deduplication using already-owned technical
    probing.

    Only complete logical identities with multiple candidates are
    technically verified.

    Unique incoming identities are returned without probing.

    TV content without a complete season/episode identity remains
    passthrough and is never collapsed here.

    Successful probes may correct resolution and video codec before
    quality ranking. Release source remains filename-derived.

    Failed probes preserve filename-derived quality.

    Equal verified scores retain the first occurrence so selection
    remains deterministic.

    No filesystem changes are performed.
    """
    groups: dict[
        tuple,
        list[MediaMetadata],
    ] = {}

    passthrough: list[MediaMetadata] = []

    for media in incoming:
        if (
            media.media_type == "tv"
            and (
                media.season is None
                or media.episode is None
            )
        ):
            passthrough.append(media)
            continue

        key = media_key(media)

        groups.setdefault(
            key,
            [],
        ).append(media)

    selected: list[MediaMetadata] = []

    for candidates in groups.values():
        if len(candidates) == 1:
            selected.append(
                candidates[0]
            )
            continue

        winner = candidates[0]
        winner_score = None

        for candidate in candidates:
            verified = candidate

            if candidate.path is not None:
                technical = probe_once(
                    candidate.path
                )

                verified = (
                    enrich_quality_from_technical(
                        candidate,
                        technical,
                    )
                )

            candidate_score = quality_score(
                verified
            )

            if (
                winner_score is None
                or candidate_score > winner_score
            ):
                winner = candidate
                winner_score = candidate_score

        selected.append(winner)

    return [
        *selected,
        *passthrough,
    ]


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

    Incoming duplicate groups with complete logical identity are
    technically verified before selecting their winning candidate.
    Unique incoming identities and unknown-TV passthrough items are
    not probed for deduplication.

    NEW items are otherwise not technically probed because technical
    quality cannot affect the absence of an existing library match.
    """
    index = LibraryIndex()

    for media in library:
        index.add(media)

    items = []

    # Technical metadata is cached only for the lifetime of this
    # queue build. The same cache is shared by incoming duplicate
    # selection and later library comparison so a winning shuttle
    # candidate is never re-probed during the same build.
    probe_cache = {}

    def probe_once(path: Path):
        resolved = Path(path).resolve()

        if resolved not in probe_cache:
            probe_cache[resolved] = probe_media(
                resolved
            )

        return probe_cache[resolved]

    deduplicated_incoming = (
        _deduplicate_incoming_verified(
            incoming,
            probe_once=probe_once,
        )
    )

    for media in deduplicated_incoming:
        existing = index.find(media)

        # Technical quality cannot change a NEW decision because
        # there is no existing library copy to compare against.
        #
        # Avoiding ffprobe here is especially important for shuttle
        # loads containing mostly new media.
        if existing is None:
            items.append(
                DecisionQueueItem(
                    incoming=media,
                    existing=None,
                    decision=decide(
                        None,
                        media,
                    ),
                )
            )

            continue

        incoming_technical = None
        existing_technical = None

        if media.path is not None:
            incoming_technical = probe_once(
                media.path
            )

        if existing.path is not None:
            existing_technical = probe_once(
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
