from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class MediaMetadata:
    media_type: str
    title: str

    year: int | None = None

    season: int | None = None
    episode: int | None = None

    resolution: str | None = None
    source: str | None = None
    video_codec: str | None = None

    container: str | None = None

    path: Path | None = None
    size: int = 0
