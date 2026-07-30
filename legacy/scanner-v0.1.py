#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


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

IGNORED_FILENAME_PARTS = {
    "sample",
    "trailer",
}

TV_PATTERNS = [
    re.compile(
        r"(?i)(?P<show>.*?)[ ._\-\[]+S(?P<season>\d{1,2})E(?P<episode>\d{1,3})"
    ),
    re.compile(
        r"(?i)(?P<show>.*?)[ ._\-\[]+(?P<season>\d{1,2})x(?P<episode>\d{1,3})"
    ),
]

YEAR_PATTERN = re.compile(r"(?<!\d)(?P<year>19\d{2}|20\d{2})(?!\d)")
SEASON_FOLDER_PATTERN = re.compile(r"(?i)\bseason[ ._-]*(?P<season>\d{1,2})\b")
RELEASE_TAG_PATTERN = re.compile(
    r"(?ix)"
    r"\b("
    r"2160p|1080p|720p|576p|480p|"
    r"web[-_. ]?dl|webrip|bluray|brrip|dvdrip|hdtv|hdrip|"
    r"x264|x265|h264|h265|hevc|av1|"
    r"aac|ac3|ddp\d?(?:\.\d)?|dts|atmos|"
    r"repack|proper|complete|"
    r"galaxytv|galaxyrg|yts(?:\.mx|\.lt|\.am)?|tgx|rarbg|rartv"
    r")\b"
)


@dataclass
class MediaItem:
    category: str
    path: str
    filename: str
    extension: str
    size_bytes: int
    title: str | None = None
    year: int | None = None
    show: str | None = None
    season: int | None = None
    episode: int | None = None
    reason: str | None = None


def clean_name(value: str) -> str:
    value = Path(value).stem
    value = re.sub(r"[\[\(].*?[\]\)]", " ", value)
    value = RELEASE_TAG_PATTERN.sub(" ", value)
    value = re.sub(r"[._]+", " ", value)
    value = re.sub(r"\s*-\s*", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -._")


def probable_show_name(file_path: Path, matched_show: str) -> str:
    cleaned_match = clean_name(matched_show)

    if len(cleaned_match) >= 2:
        return cleaned_match

    parent = file_path.parent.name
    parent = SEASON_FOLDER_PATTERN.sub("", parent)
    cleaned_parent = clean_name(parent)

    if cleaned_parent:
        return cleaned_parent

    return "Unknown Show"


def classify_video(file_path: Path, shuttle_root: Path) -> MediaItem:
    relative_path = file_path.relative_to(shuttle_root)
    filename = file_path.name

    try:
        size_bytes = file_path.stat().st_size
    except OSError:
        size_bytes = 0

    searchable = str(relative_path)

    for pattern in TV_PATTERNS:
        match = pattern.search(searchable)
        if match:
            show = probable_show_name(file_path, match.group("show"))

            return MediaItem(
                category="tv",
                path=str(relative_path),
                filename=filename,
                extension=file_path.suffix.lower(),
                size_bytes=size_bytes,
                show=show,
                season=int(match.group("season")),
                episode=int(match.group("episode")),
            )

    season_match = SEASON_FOLDER_PATTERN.search(searchable)
    if season_match:
        parent_parts = list(relative_path.parts[:-1])
        possible_show = parent_parts[0] if parent_parts else file_path.parent.name

        return MediaItem(
            category="tv_unknown_episode",
            path=str(relative_path),
            filename=filename,
            extension=file_path.suffix.lower(),
            size_bytes=size_bytes,
            show=clean_name(possible_show),
            season=int(season_match.group("season")),
            reason="Season detected but no episode number was found",
        )

    year_matches = list(YEAR_PATTERN.finditer(searchable))
    if year_matches:
        match = year_matches[-1]
        year = int(match.group("year"))

        title_source = filename[: match.start()]
        title = clean_name(title_source)

        if not title:
            title = clean_name(file_path.parent.name)

        return MediaItem(
            category="movie",
            path=str(relative_path),
            filename=filename,
            extension=file_path.suffix.lower(),
            size_bytes=size_bytes,
            title=title or "Unknown Movie",
            year=year,
        )

    return MediaItem(
        category="unknown",
        path=str(relative_path),
        filename=filename,
        extension=file_path.suffix.lower(),
        size_bytes=size_bytes,
        title=clean_name(file_path.parent.name),
        reason="No TV episode pattern or reliable movie year detected",
    )


def should_ignore_directory(directory_name: str) -> bool:
    return directory_name.casefold() in IGNORED_DIRECTORIES


def should_ignore_file(file_path: Path) -> bool:
    lower_name = file_path.name.casefold()

    if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
        return True

    return any(part in lower_name for part in IGNORED_FILENAME_PARTS)


def iter_video_files(root: Path) -> Iterable[Path]:
    for current_root, directory_names, filenames in os.walk(root):
        directory_names[:] = [
            directory
            for directory in directory_names
            if not should_ignore_directory(directory)
        ]

        for filename in filenames:
            file_path = Path(current_root) / filename

            if not should_ignore_file(file_path):
                yield file_path


def format_size(size_bytes: int) -> str:
    size = float(size_bytes)

    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size_bytes} B"


def write_text_report(
    report_path: Path,
    shuttle_root: Path,
    items: list[MediaItem],
    started_at: datetime,
    finished_at: datetime,
) -> None:
    counts = Counter(item.category for item in items)
    total_size = sum(item.size_bytes for item in items)

    tv_shows: dict[str, list[MediaItem]] = defaultdict(list)
    movies: list[MediaItem] = []
    uncertain_tv: list[MediaItem] = []
    unknown: list[MediaItem] = []

    for item in items:
        if item.category == "tv":
            tv_shows[item.show or "Unknown Show"].append(item)
        elif item.category == "movie":
            movies.append(item)
        elif item.category == "tv_unknown_episode":
            uncertain_tv.append(item)
        else:
            unknown.append(item)

    with report_path.open("w", encoding="utf-8") as report:
        report.write("=" * 72 + "\n")
        report.write("DECKFLIX SHUTTLE SCAN REPORT\n")
        report.write("=" * 72 + "\n\n")

        report.write(f"Shuttle:       {shuttle_root}\n")
        report.write(f"Started:       {started_at.isoformat(timespec='seconds')}\n")
        report.write(f"Finished:      {finished_at.isoformat(timespec='seconds')}\n")
        report.write(f"Video files:   {len(items)}\n")
        report.write(f"Video size:    {format_size(total_size)}\n\n")

        report.write("SUMMARY\n")
        report.write("-" * 72 + "\n")
        report.write(f"Probable movies:           {counts['movie']}\n")
        report.write(f"Recognised TV episodes:    {counts['tv']}\n")
        report.write(f"TV files needing review:   {counts['tv_unknown_episode']}\n")
        report.write(f"Unknown video files:       {counts['unknown']}\n")
        report.write(f"Recognised TV shows:       {len(tv_shows)}\n\n")

        report.write("TV SHOWS\n")
        report.write("-" * 72 + "\n")

        for show in sorted(tv_shows, key=str.casefold):
            episodes = tv_shows[show]
            seasons: dict[int, list[int]] = defaultdict(list)

            for episode in episodes:
                if episode.season is not None and episode.episode is not None:
                    seasons[episode.season].append(episode.episode)

            report.write(f"\n{show}\n")

            for season in sorted(seasons):
                episode_numbers = sorted(set(seasons[season]))
                report.write(
                    f"  Season {season:02d}: "
                    f"{len(episode_numbers)} recognised episode(s) "
                    f"[{', '.join(str(number) for number in episode_numbers)}]\n"
                )

        report.write("\n\nPROBABLE MOVIES\n")
        report.write("-" * 72 + "\n")

        for movie in sorted(
            movies,
            key=lambda item: ((item.title or "").casefold(), item.year or 0),
        ):
            report.write(
                f"{movie.title} ({movie.year})\n"
                f"  {movie.path}\n"
                f"  {format_size(movie.size_bytes)}\n"
            )

        report.write("\n\nTV FILES NEEDING REVIEW\n")
        report.write("-" * 72 + "\n")

        for item in uncertain_tv:
            report.write(
                f"{item.path}\n"
                f"  Reason: {item.reason}\n"
            )

        report.write("\n\nUNKNOWN VIDEO FILES\n")
        report.write("-" * 72 + "\n")

        for item in unknown:
            report.write(
                f"{item.path}\n"
                f"  Reason: {item.reason}\n"
            )

        report.write("\n\nIMPORTANT\n")
        report.write("-" * 72 + "\n")
        report.write("This scanner is read-only.\n")
        report.write("No media was copied, moved, renamed, replaced, or deleted.\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only DeckFlix shuttle media scanner"
    )
    parser.add_argument(
        "--shuttle",
        default="/data/shuttle",
        help="Mounted shuttle path",
    )
    parser.add_argument(
        "--output",
        default="/data/library1/deckflix-logs",
        help="Report output directory",
    )

    args = parser.parse_args()

    shuttle_root = Path(args.shuttle)
    output_root = Path(args.output)

    if not shuttle_root.exists():
        print(f"ERROR: Shuttle path does not exist: {shuttle_root}", file=sys.stderr)
        return 1

    if not shuttle_root.is_mount():
        print(
            f"ERROR: {shuttle_root} is not currently a mounted filesystem.",
            file=sys.stderr,
        )
        print(
            "The scan was stopped to prevent accidentally scanning an empty folder.",
            file=sys.stderr,
        )
        return 1

    output_root.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now()
    timestamp = started_at.strftime("%Y-%m-%d_%H-%M-%S")

    print("=" * 60)
    print("DECKFLIX SHUTTLE SCANNER")
    print("=" * 60)
    print(f"Scanning: {shuttle_root}")
    print("Mode:     READ ONLY")
    print()

    items: list[MediaItem] = []

    for index, file_path in enumerate(iter_video_files(shuttle_root), start=1):
        item = classify_video(file_path, shuttle_root)
        items.append(item)

        if index % 100 == 0:
            print(f"Scanned {index} video files...")

    finished_at = datetime.now()

    json_path = output_root / f"shuttle-scan-{timestamp}.json"
    text_path = output_root / f"shuttle-scan-{timestamp}.txt"

    payload = {
        "scanner_version": "0.1.0",
        "read_only": True,
        "shuttle_path": str(shuttle_root),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "total_video_files": len(items),
        "total_video_bytes": sum(item.size_bytes for item in items),
        "counts": dict(Counter(item.category for item in items)),
        "items": [asdict(item) for item in items],
    }

    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, indent=2, ensure_ascii=False)

    write_text_report(
        report_path=text_path,
        shuttle_root=shuttle_root,
        items=items,
        started_at=started_at,
        finished_at=finished_at,
    )

    counts = Counter(item.category for item in items)

    print()
    print("=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"Video files:        {len(items)}")
    print(f"Probable movies:    {counts['movie']}")
    print(f"TV episodes:        {counts['tv']}")
    print(f"TV needs review:    {counts['tv_unknown_episode']}")
    print(f"Unknown videos:     {counts['unknown']}")
    print()
    print(f"Text report: {text_path}")
    print(f"JSON report: {json_path}")
    print()
    print("No media files were changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
