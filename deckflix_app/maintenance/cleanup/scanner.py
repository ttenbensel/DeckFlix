from pathlib import Path

from .models import CleanupReport


VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".mov",
}

SUBTITLE_EXTENSIONS = {
    ".srt",
    ".sub",
    ".idx",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

METADATA_EXTENSIONS = {
    ".nfo",
    ".xml",
}


def scan_cleanup(
    path: Path,
) -> CleanupReport:

    report = CleanupReport(
        path=path,
    )

    for item in path.rglob("*"):

        if item.is_dir():

            try:
                next(item.iterdir())

            except StopIteration:
                report.empty_directories += 1

            continue


        size = item.stat().st_size

        report.total_bytes += size

        name = item.name.lower()
        suffix = item.suffix.lower()


        if suffix in VIDEO_EXTENSIONS:

            report.video_files += 1


        elif (
            "sample" in item.parts
            or "sample" in name
        ):

            report.sample_files += 1

            if len(report.sample_examples) < 10:
                report.sample_examples.append(
                    item
                )


        elif suffix in SUBTITLE_EXTENSIONS:

            report.subtitle_files += 1

            if len(report.subtitle_examples) < 10:
                report.subtitle_examples.append(
                    item
                )


        elif suffix in IMAGE_EXTENSIONS:

            report.image_files += 1

            if len(report.image_examples) < 10:
                report.image_examples.append(
                    item
                )


        elif suffix in METADATA_EXTENSIONS:

            report.metadata_files += 1


        else:

            report.other_files += 1

            if len(report.other_examples) < 10:
                report.other_examples.append(
                    item
                )


    return report
