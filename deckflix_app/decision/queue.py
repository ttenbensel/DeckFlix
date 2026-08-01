from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from deckflix_app.library import LibraryIndex
from deckflix_app.media import MediaInfo, inspect_media
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.scanner import scan_videos

from .actions import Action
from .engine import decide
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


def scan_metadata(path: Path) -> list[MediaMetadata]:
    return [
        metadata_from_media_info(inspect_media(file))
        for file in scan_videos(path)
    ]


def build_decision_queue(
    *,
    incoming: list[MediaMetadata],
    library: list[MediaMetadata],
) -> DecisionQueue:
    index = LibraryIndex()

    for media in library:
        index.add(media)

    items = []

    for media in incoming:
        existing = index.find(media)

        items.append(
            DecisionQueueItem(
                incoming=media,
                existing=existing,
                decision=decide(existing, media),
            )
        )

    return DecisionQueue(items=items)


def build_decision_queue_from_paths(
    *,
    shuttle_path: Path,
    movie_libraries: list[Path],
    tv_libraries: list[Path],
) -> DecisionQueue:
    incoming = scan_metadata(shuttle_path)

    library = []

    for path in [*movie_libraries, *tv_libraries]:
        library.extend(scan_metadata(path))

    return build_decision_queue(
        incoming=incoming,
        library=library,
    )
