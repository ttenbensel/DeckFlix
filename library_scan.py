#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/opt/deckflix")

from scanner import classify_video, format_size, iter_video_files


LIBRARIES = {
    "movies": Path("/data/library1/movie"),
    "library2": Path("/data/library2"),
}

OUTPUT_DIR = Path("/data/library1/deckflix-logs")


def main() -> int:
    missing = [str(path) for path in LIBRARIES.values() if not path.exists()]

    if missing:
        print("ERROR: Missing library paths:")
        for path in missing:
            print(f"  {path}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    started = datetime.now()
    timestamp = started.strftime("%Y-%m-%d_%H-%M-%S")

    records = []

    print("=" * 60)
    print("DECKFLIX LIBRARY SCANNER")
    print("=" * 60)
    print("Mode: READ ONLY")
    print()

    total_scanned = 0

    for library_name, library_path in LIBRARIES.items():
        print(f"Scanning {library_name}: {library_path}")

        library_count = 0

        for file_path in iter_video_files(library_path):
            item = classify_video(file_path, library_path)
            record = asdict(item)
            record["library"] = library_name
            record["library_root"] = str(library_path)
            records.append(record)

            library_count += 1
            total_scanned += 1

            if library_count % 500 == 0:
                print(f"  Scanned {library_count} video files...")

        print(f"  Completed: {library_count} video files")
        print()

    finished = datetime.now()
    counts = Counter(record["category"] for record in records)
    total_size = sum(record["size_bytes"] for record in records)

    json_path = OUTPUT_DIR / f"library-scan-{timestamp}.json"
    text_path = OUTPUT_DIR / f"library-scan-{timestamp}.txt"

    payload = {
        "scanner_version": "0.1.0",
        "read_only": True,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "libraries": {
            name: str(path)
            for name, path in LIBRARIES.items()
        },
        "total_video_files": len(records),
        "total_video_bytes": total_size,
        "counts": dict(counts),
        "items": records,
    }

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    with text_path.open("w", encoding="utf-8") as report:
        report.write("=" * 72 + "\n")
        report.write("DECKFLIX LIBRARY SCAN REPORT\n")
        report.write("=" * 72 + "\n\n")
        report.write(f"Started:      {started.isoformat(timespec='seconds')}\n")
        report.write(f"Finished:     {finished.isoformat(timespec='seconds')}\n")
        report.write(f"Video files:  {len(records)}\n")
        report.write(f"Video size:   {format_size(total_size)}\n\n")

        report.write("CLASSIFICATION\n")
        report.write("-" * 72 + "\n")
        report.write(f"Probable movies:         {counts['movie']}\n")
        report.write(f"Recognised TV episodes:  {counts['tv']}\n")
        report.write(f"TV needing review:       {counts['tv_unknown_episode']}\n")
        report.write(f"Unknown videos:          {counts['unknown']}\n\n")

        report.write("LIBRARIES\n")
        report.write("-" * 72 + "\n")

        for name, path in LIBRARIES.items():
            count = sum(1 for record in records if record["library"] == name)
            report.write(f"{name}: {path}\n")
            report.write(f"  Video files: {count}\n")

        report.write("\nNo media files were changed.\n")

    print("=" * 60)
    print("LIBRARY SCAN COMPLETE")
    print("=" * 60)
    print(f"Video files:       {len(records)}")
    print(f"Probable movies:   {counts['movie']}")
    print(f"TV episodes:       {counts['tv']}")
    print(f"TV needs review:   {counts['tv_unknown_episode']}")
    print(f"Unknown videos:    {counts['unknown']}")
    print()
    print(f"Text report: {text_path}")
    print(f"JSON report: {json_path}")
    print()
    print("No media files were changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
