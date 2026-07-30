from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator


VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".m4v",
    ".mov",
    ".wmv",
    ".ts",
    ".mpg",
    ".mpeg",
}

IGNORED_DIRECTORIES = {
    "$recycle.bin",
    "system volume information",
    ".trash",
    ".trashes",
    "@eadir",
}

IGNORED_FILE_PARTS = {
    "sample",
    "trailer",
}


def iter_video_files(root: Path) -> Iterator[Path]:
    for current_root, directories, filenames in os.walk(root):
        directories[:] = [
            directory
            for directory in directories
            if directory.casefold() not in IGNORED_DIRECTORIES
        ]

        for filename in filenames:
            path = Path(current_root) / filename
            lower_name = filename.casefold()

            if path.suffix.casefold() not in VIDEO_EXTENSIONS:
                continue

            if any(part in lower_name for part in IGNORED_FILE_PARTS):
                continue

            yield path
