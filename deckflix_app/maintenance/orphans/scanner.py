from pathlib import Path

from .models import (
    OrphanCandidate,
    OrphanType,
)


VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".mov",
}

SUBTITLE_EXTENSIONS = {
    ".srt",
    ".sub",
    ".ass",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

METADATA_EXTENSIONS = {
    ".nfo",
}

JUNK_EXTENSIONS = {
    ".txt",
    ".torrent",
    ".url",
}


def scan_folder_contents(
    folder: Path,
):

    counts = {
        "video": 0,
        "subtitle": 0,
        "image": 0,
        "metadata": 0,
        "junk": 0,
    }

    for item in folder.rglob("*"):

        if not item.is_file():
            continue

        suffix = item.suffix.lower()

        if suffix in VIDEO_EXTENSIONS:
            counts["video"] += 1

        elif suffix in SUBTITLE_EXTENSIONS:
            counts["subtitle"] += 1

        elif suffix in IMAGE_EXTENSIONS:
            counts["image"] += 1

        elif suffix in METADATA_EXTENSIONS:
            counts["metadata"] += 1

        elif suffix in JUNK_EXTENSIONS:
            counts["junk"] += 1

    return counts


def scan_orphans(
    source: Path,
    destination: Path,
) -> list[OrphanCandidate]:

    results = []

    destination_names = {
        folder.name
        for folder in destination.iterdir()
        if folder.is_dir()
    }


    for folder in source.iterdir():

        if not folder.is_dir():
            continue


        counts = scan_folder_contents(
            folder
        )


        #
        # Source still has media
        #
        if counts["video"] > 0:
            continue


        #
        # Media already migrated
        #
        if folder.name in destination_names:

            results.append(
                OrphanCandidate(
                    path=folder,
                    classification=(
                        OrphanType.MIGRATION_LEFTOVER
                    ),
                    video_files=counts["video"],
                    subtitle_files=counts["subtitle"],
                    image_files=counts["image"],
                    metadata_files=counts["metadata"],
                    junk_files=counts["junk"],
                    reason=(
                        "Media exists in destination "
                        "library"
                    ),
                )
            )

            continue


        #
        # Release junk only
        #
        if (
            counts["junk"] > 0
            and counts["subtitle"] == 0
            and counts["image"] == 0
            and counts["metadata"] == 0
        ):

            results.append(
                OrphanCandidate(
                    path=folder,
                    classification=(
                        OrphanType.RELEASE_JUNK
                    ),
                    video_files=counts["video"],
                    subtitle_files=counts["subtitle"],
                    image_files=counts["image"],
                    metadata_files=counts["metadata"],
                    junk_files=counts["junk"],
                    reason=(
                        "Release junk without "
                        "playable media"
                    ),
                )
            )

            continue


        #
        # Completely empty movie folder
        #
        if (
            counts["subtitle"] == 0
            and counts["image"] == 0
            and counts["metadata"] == 0
            and counts["junk"] == 0
        ):

            results.append(
                OrphanCandidate(
                    path=folder,
                    classification=(
                        OrphanType.ORPHAN_MOVIE
                    ),
                    video_files=counts["video"],
                    subtitle_files=counts["subtitle"],
                    image_files=counts["image"],
                    metadata_files=counts["metadata"],
                    junk_files=counts["junk"],
                    reason=(
                        "No media or "
                        "supporting files"
                    ),
                )
            )


    return results
