"""Raw filesystem scan results."""

from __future__ import annotations

from dataclasses import dataclass, field

from deckflix_app.inventory.models import (
    Drive,
    Library,
    MediaItem,
    ScanRecord,
)


@dataclass(slots=True)
class ScanResult:
    """Represents the raw output of a filesystem scan.

    This object deliberately contains no business logic. It simply
    captures everything discovered during a scan before the inventory
    is built.
    """

    drives: list[Drive] = field(default_factory=list)
    libraries: list[Library] = field(default_factory=list)
    media: list[MediaItem] = field(default_factory=list)
    record: ScanRecord | None = None
