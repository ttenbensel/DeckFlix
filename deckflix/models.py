from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class ParsedMedia:
    media_type: str
    title: str | None = None
    year: int | None = None
    show: str | None = None
    season: int | None = None
    episode: int | None = None
    confidence: int = 0
    parser: str = "unknown"
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
