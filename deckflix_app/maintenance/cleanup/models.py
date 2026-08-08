from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class CleanupReport:
    path: Path

    video_files: int = 0
    sample_files: int = 0
    subtitle_files: int = 0
    image_files: int = 0
    metadata_files: int = 0
    other_files: int = 0
    empty_directories: int = 0

    total_bytes: int = 0

    sample_examples: list[Path] = field(
        default_factory=list
    )

    other_examples: list[Path] = field(
        default_factory=list
    )

    subtitle_examples: list[Path] = field(
        default_factory=list
    )

    image_examples: list[Path] = field(
        default_factory=list
    )
