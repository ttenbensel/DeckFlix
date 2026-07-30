from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from deckflix.parser.media_parser import parse_media
from deckflix.scanner.filesystem import iter_video_files


def scan_path(root: Path) -> dict:
    started = datetime.now()
    items = []

    for index, full_path in enumerate(iter_video_files(root), start=1):
        relative_path = full_path.relative_to(root)
        parsed = parse_media(relative_path)

        try:
            size_bytes = full_path.stat().st_size
        except OSError:
            size_bytes = 0

        record = parsed.to_dict()
        record.update(
            {
                "path": str(relative_path),
                "filename": full_path.name,
                "extension": full_path.suffix.casefold(),
                "size_bytes": size_bytes,
            }
        )
        items.append(record)

        if index % 250 == 0:
            print(f"Scanned {index} video files...")

    counts = Counter(item["media_type"] for item in items)

    return {
        "deckflix_version": "0.2.0",
        "read_only": True,
        "root": str(root),
        "started_at": started.isoformat(),
        "finished_at": datetime.now().isoformat(),
        "total_video_files": len(items),
        "total_video_bytes": sum(item["size_bytes"] for item in items),
        "counts": dict(counts),
        "items": items,
    }


def save_inventory(payload: dict, output_directory: Path, prefix: str) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = output_directory / f"{prefix}-{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    return output_path
