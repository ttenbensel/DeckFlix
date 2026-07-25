from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class IndexedMedia:
    title: str
    media_type: str
    library: str
    path: Path

    year: int | None = None

    resolution: str = "unknown"
    source: str = "unknown"
    codec: str = "unknown"
    quality_score: int = 0
    size: int = 0

    audio: str | None = None

    @property
    def duplicate_key(self):
        """
        Normalised key used when detecting duplicates.
        """

        title = (
            self.title
            .lower()
            .replace(".", " ")
            .replace("_", " ")
            .strip()
        )

        title = " ".join(title.split())

        return (
            title,
            self.year,
            self.media_type,
        )
