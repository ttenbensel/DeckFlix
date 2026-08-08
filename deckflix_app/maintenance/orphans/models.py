from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class OrphanType(str, Enum):
    MIGRATION_LEFTOVER = "MIGRATION_LEFTOVER"
    RELEASE_JUNK = "RELEASE_JUNK"
    ORPHAN_MOVIE = "ORPHAN_MOVIE"


@dataclass(slots=True)
class OrphanCandidate:
    path: Path
    classification: OrphanType
    video_files: int
    subtitle_files: int
    image_files: int
    metadata_files: int
    junk_files: int
    reason: str
