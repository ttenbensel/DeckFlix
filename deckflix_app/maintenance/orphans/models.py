from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class OrphanType(str, Enum):
    MIGRATION_LEFTOVER = "MIGRATION_LEFTOVER"
    RELEASE_JUNK = "RELEASE_JUNK"
    ORPHAN_MOVIE = "ORPHAN_MOVIE"
    COLLECTION_CONTAINER = "COLLECTION_CONTAINER"


@dataclass(slots=True)
class OrphanCandidate:
    path: Path
    classification: OrphanType
    reason: str

    video_files: int = 0
    subtitle_files: int = 0
    image_files: int = 0
    metadata_files: int = 0
    junk_files: int = 0
