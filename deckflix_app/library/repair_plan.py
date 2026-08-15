from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .audit import (
    LibraryAudit,
    LibraryAuditEntry,
    LibraryIssue,
)


class LibraryRepairStatus(str, Enum):
    READY = "READY"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


class LibraryRepairAction(str, Enum):
    MOVE = "MOVE"
    MOVE_RENAME = "MOVE_RENAME"
    REVIEW = "REVIEW"


@dataclass(frozen=True, slots=True)
class LibraryRepairItem:
    entry: LibraryAuditEntry
    source: Path
    destination: Path | None
    action: LibraryRepairAction
    status: LibraryRepairStatus
    reason: str

    @property
    def media(self):
        return self.entry.media


@dataclass(frozen=True, slots=True)
class LibraryRepairPlan:
    items: tuple[LibraryRepairItem, ...]

    def count(
        self,
        status: LibraryRepairStatus,
    ) -> int:
        return sum(
            1
            for item in self.items
            if item.status is status
        )

    @property
    def ready(self) -> tuple[LibraryRepairItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.status is LibraryRepairStatus.READY
        )

    @property
    def review(self) -> tuple[LibraryRepairItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.status is LibraryRepairStatus.REVIEW
        )

    @property
    def blocked(self) -> tuple[LibraryRepairItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.status is LibraryRepairStatus.BLOCKED
        )


def _safe_component(
    value: str,
) -> str:
    value = value.strip()

    for character in '<>:"/\\|?*':
        value = value.replace(
            character,
            " ",
        )

    return " ".join(
        value.split()
    )


def movie_destination(
    entry: LibraryAuditEntry,
    movies_root: Path,
) -> Path | None:
    media = entry.media

    if (
        not media.title.strip()
        or media.year is None
    ):
        return None

    title = _safe_component(
        media.title
    )

    folder = (
        f"{title} ({media.year})"
    )

    suffix = entry.path.suffix.lower()

    filename = (
        f"{folder}{suffix}"
    )

    return (
        Path(movies_root)
        / folder
        / filename
    )


def tv_destination(
    entry: LibraryAuditEntry,
    tv_root: Path,
) -> Path | None:
    media = entry.media

    if (
        not media.title.strip()
        or media.season is None
        or media.episode is None
    ):
        return None

    title = _safe_component(
        media.title
    )

    suffix = entry.path.suffix.lower()

    filename = (
        f"{title} "
        f"S{media.season:02d}"
        f"E{media.episode:02d}"
        f"{suffix}"
    )

    return (
        Path(tv_root)
        / title
        / f"Season {media.season:02d}"
        / filename
    )


def destination_for(
    entry: LibraryAuditEntry,
    movies_root: Path,
    tv_root: Path,
) -> Path | None:
    if entry.media.media_type == "movie":
        return movie_destination(
            entry,
            movies_root,
        )

    if entry.media.media_type == "tv":
        return tv_destination(
            entry,
            tv_root,
        )

    return None


def _requires_review(
    entry: LibraryAuditEntry,
) -> str | None:
    media = entry.media

    if LibraryIssue.WEAK_METADATA in entry.issues:
        return (
            "Metadata is not strong enough "
            "for an automatic destination."
        )

    if not media.title.strip():
        return "Media title is missing."

    if media.media_type == "movie":
        if media.year is None:
            return "Movie year is unknown."

        return None

    if media.media_type == "tv":
        if (
            media.season is None
            or media.episode is None
        ):
            return (
                "TV season or episode "
                "number is unknown."
            )

        # Specials and episode zero are valid,
        # but require operator review before an
        # existing-library repair is approved.
        if (
            media.season == 0
            or media.episode == 0
            or media.content_type == "special"
        ):
            return (
                "TV special or episode zero "
                "requires operator review."
            )

        return None

    return "Media type is unknown."


def _action_for(
    source: Path,
    destination: Path,
) -> LibraryRepairAction:
    if source.name == destination.name:
        return LibraryRepairAction.MOVE

    return LibraryRepairAction.MOVE_RENAME


def _make_item(
    *,
    entry: LibraryAuditEntry,
    destination: Path | None,
    status: LibraryRepairStatus,
    action: LibraryRepairAction,
    reason: str,
) -> LibraryRepairItem:
    return LibraryRepairItem(
        entry=entry,
        source=entry.path,
        destination=destination,
        action=action,
        status=status,
        reason=reason,
    )


def build_library_repair_plan(
    audit: LibraryAudit,
    *,
    movies_root: Path = Path(
        "/data/library1/movie"
    ),
    tv_root: Path = Path(
        "/data/library2/tv"
    ),
) -> LibraryRepairPlan:
    """
    Build a read-only repair proposal for genuinely
    misplaced existing-library media.

    This function performs no filesystem writes.

    It does not move, rename, copy, delete, create,
    modify, or submit media to Jellyfin.

    REVIEW items remain REVIEW until an explicit
    operator-resolution layer converts them into
    a new validated READY item.
    """
    movies_root = Path(
        movies_root
    ).resolve()

    tv_root = Path(
        tv_root
    ).resolve()

    items: list[
        LibraryRepairItem
    ] = []

    proposed_destinations: dict[
        Path,
        list[LibraryAuditEntry],
    ] = {}

    candidates = [
        entry
        for entry in audit.entries
        if LibraryIssue.MISPLACED
        in entry.issues
    ]

    for entry in candidates:
        destination = destination_for(
            entry,
            movies_root,
            tv_root,
        )

        if destination is not None:
            proposed_destinations.setdefault(
                destination,
                [],
            ).append(
                entry
            )

    for entry in candidates:
        source = entry.path

        destination = destination_for(
            entry,
            movies_root,
            tv_root,
        )

        review_reason = _requires_review(
            entry
        )

        if destination is None:
            items.append(
                _make_item(
                    entry=entry,
                    destination=None,
                    action=LibraryRepairAction.REVIEW,
                    status=LibraryRepairStatus.REVIEW,
                    reason=(
                        review_reason
                        or
                        "Safe destination could "
                        "not be determined."
                    ),
                )
            )
            continue

        collisions = (
            proposed_destinations[
                destination
            ]
        )

        if len(collisions) > 1:
            items.append(
                _make_item(
                    entry=entry,
                    destination=destination,
                    action=LibraryRepairAction.REVIEW,
                    status=LibraryRepairStatus.BLOCKED,
                    reason=(
                        "Multiple source files "
                        "propose the same "
                        "destination."
                    ),
                )
            )
            continue

        if destination.exists():
            items.append(
                _make_item(
                    entry=entry,
                    destination=destination,
                    action=LibraryRepairAction.REVIEW,
                    status=LibraryRepairStatus.BLOCKED,
                    reason=(
                        "Destination already exists."
                    ),
                )
            )
            continue

        if review_reason is not None:
            items.append(
                _make_item(
                    entry=entry,
                    destination=destination,
                    action=LibraryRepairAction.REVIEW,
                    status=LibraryRepairStatus.REVIEW,
                    reason=review_reason,
                )
            )
            continue

        items.append(
            _make_item(
                entry=entry,
                destination=destination,
                action=_action_for(
                    source,
                    destination,
                ),
                status=LibraryRepairStatus.READY,
                reason=(
                    "Media type does not match "
                    "its current library root."
                ),
            )
        )

    return LibraryRepairPlan(
        items=tuple(items)
    )


def resolve_review_item(
    item: LibraryRepairItem,
    *,
    title: str | None = None,
    season: int | None = None,
    episode: int | None = None,
    content_type: str | None = None,
    destination: Path | None = None,
) -> LibraryRepairItem:
    """
    Create a new READY repair item from an explicit
    operator resolution.

    This function performs no filesystem writes.

    The destination must be supplied by the caller
    only when it has already been constructed through
    DeckFlix's safe destination builders.

    Arbitrary filesystem paths are deliberately not
    accepted as a resolution mechanism by the UI.
    """
    if item.status is not LibraryRepairStatus.REVIEW:
        raise ValueError(
            "Only REVIEW items can be resolved."
        )

    media = item.media

    if title is not None:
        title = title.strip()

        if not title:
            raise ValueError(
                "Resolved title cannot be empty."
            )

    else:
        title = media.title.strip()

    if not title:
        raise ValueError(
            "Resolved title cannot be empty."
        )

    if media.media_type == "movie":
        if media.year is None:
            raise ValueError(
                "Movie year is required."
            )

    elif media.media_type == "tv":
        if season is None:
            raise ValueError(
                "Resolved TV season is required."
            )

        if episode is None:
            raise ValueError(
                "Resolved TV episode is required."
            )

        if season < 0:
            raise ValueError(
                "Resolved TV season cannot be negative."
            )

        if episode < 0:
            raise ValueError(
                "Resolved TV episode cannot be negative."
            )

    else:
        raise ValueError(
            "Resolved media type is unsupported."
        )

    if content_type is not None:
        content_type = (
            content_type.strip()
            or None
        )

    if destination is None:
        raise ValueError(
            "A safe resolved destination is required."
        )

    destination = Path(
        destination
    ).resolve()

    if destination.exists():
        raise ValueError(
            "Resolved destination already exists."
        )

    return LibraryRepairItem(
        entry=item.entry,
        source=item.source,
        destination=destination,
        action=_action_for(
            item.source,
            destination,
        ),
        status=LibraryRepairStatus.READY,
        reason=(
            "Explicit operator resolution "
            "validated for repair."
        ),
    )
