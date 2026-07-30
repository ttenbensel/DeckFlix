#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


LOG_DIR = Path("/data/library1/deckflix-logs")


def latest_report(pattern: str) -> Path:
    reports = sorted(
        LOG_DIR.glob(pattern),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not reports:
        raise FileNotFoundError(f"No report matching {pattern}")

    return reports[0]


def normalise(value: str | None) -> str:
    if not value:
        return ""

    value = value.casefold()
    value = re.sub(r"\bthe\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def movie_key(item: dict) -> tuple[str, int | None]:
    return normalise(item.get("title")), item.get("year")


def tv_key(item: dict) -> tuple[str, int | None, int | None]:
    return (
        normalise(item.get("show")),
        item.get("season"),
        item.get("episode"),
    )


def main() -> int:
    shuttle_path = latest_report("shuttle-scan-*.json")
    library_path = latest_report("library-scan-*.json")

    with shuttle_path.open("r", encoding="utf-8") as handle:
        shuttle = json.load(handle)

    with library_path.open("r", encoding="utf-8") as handle:
        library = json.load(handle)

    library_movies = {
        movie_key(item): item
        for item in library["items"]
        if item["category"] == "movie"
    }

    library_tv = {
        tv_key(item): item
        for item in library["items"]
        if item["category"] == "tv"
    }

    results = []

    for item in shuttle["items"]:
        category = item["category"]
        status = "review"
        existing = None

        if category == "movie":
            key = movie_key(item)

            if key in library_movies:
                status = "duplicate"
                existing = library_movies[key]
            else:
                status = "new"

        elif category == "tv":
            key = tv_key(item)

            if key in library_tv:
                status = "duplicate"
                existing = library_tv[key]
            else:
                status = "new"

        elif category in {"tv_unknown_episode", "unknown"}:
            status = "review"

        results.append(
            {
                "status": status,
                "category": category,
                "shuttle_item": item,
                "existing_item": existing,
            }
        )

    counts = Counter(result["status"] for result in results)
    category_counts = defaultdict(Counter)

    for result in results:
        category_counts[result["category"]][result["status"]] += 1

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    json_output = LOG_DIR / f"comparison-{timestamp}.json"
    text_output = LOG_DIR / f"comparison-{timestamp}.txt"

    payload = {
        "comparison_version": "0.1.0",
        "read_only": True,
        "created_at": datetime.now().isoformat(),
        "shuttle_report": str(shuttle_path),
        "library_report": str(library_path),
        "counts": dict(counts),
        "results": results,
    }

    with json_output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    with text_output.open("w", encoding="utf-8") as report:
        report.write("=" * 72 + "\n")
        report.write("DECKFLIX SHUTTLE COMPARISON\n")
        report.write("=" * 72 + "\n\n")

        report.write(f"Shuttle report: {shuttle_path.name}\n")
        report.write(f"Library report: {library_path.name}\n\n")

        report.write("SUMMARY\n")
        report.write("-" * 72 + "\n")
        report.write(f"New media:       {counts['new']}\n")
        report.write(f"Duplicates:      {counts['duplicate']}\n")
        report.write(f"Needs review:    {counts['review']}\n\n")

        report.write("BY CLASSIFICATION\n")
        report.write("-" * 72 + "\n")

        for category in sorted(category_counts):
            values = category_counts[category]
            report.write(
                f"{category}: "
                f"{values['new']} new, "
                f"{values['duplicate']} duplicate, "
                f"{values['review']} review\n"
            )

        report.write("\n\nNEW MOVIES\n")
        report.write("-" * 72 + "\n")

        for result in results:
            item = result["shuttle_item"]

            if result["status"] == "new" and item["category"] == "movie":
                report.write(
                    f"{item.get('title')} ({item.get('year')})\n"
                    f"  {item['path']}\n"
                )

        report.write("\n\nNEW TV EPISODES\n")
        report.write("-" * 72 + "\n")

        grouped_tv = defaultdict(list)

        for result in results:
            item = result["shuttle_item"]

            if result["status"] == "new" and item["category"] == "tv":
                grouped_tv[item.get("show") or "Unknown Show"].append(item)

        for show in sorted(grouped_tv, key=str.casefold):
            episodes = sorted(
                grouped_tv[show],
                key=lambda item: (
                    item.get("season") or 0,
                    item.get("episode") or 0,
                ),
            )

            report.write(f"\n{show}: {len(episodes)} new episode(s)\n")

            by_season = defaultdict(list)

            for episode in episodes:
                by_season[episode.get("season")].append(
                    episode.get("episode")
                )

            for season in sorted(by_season, key=lambda value: value or 0):
                numbers = sorted(
                    number
                    for number in by_season[season]
                    if number is not None
                )

                report.write(
                    f"  Season {season}: "
                    f"{', '.join(str(number) for number in numbers)}\n"
                )

        report.write("\n\nDUPLICATES\n")
        report.write("-" * 72 + "\n")

        for result in results:
            if result["status"] != "duplicate":
                continue

            incoming = result["shuttle_item"]
            existing = result["existing_item"]

            report.write(f"Incoming: {incoming['path']}\n")
            report.write(f"Existing: {existing['path']}\n\n")

        report.write("\nNEEDS REVIEW\n")
        report.write("-" * 72 + "\n")

        for result in results:
            if result["status"] == "review":
                item = result["shuttle_item"]
                report.write(
                    f"{item['path']}\n"
                    f"  Reason: {item.get('reason') or 'Classification uncertain'}\n"
                )

        report.write("\nNo media files were changed.\n")

    print("=" * 60)
    print("DECKFLIX COMPARISON COMPLETE")
    print("=" * 60)
    print(f"New media:      {counts['new']}")
    print(f"Duplicates:     {counts['duplicate']}")
    print(f"Needs review:   {counts['review']}")
    print()
    print(f"Text report: {text_output}")
    print(f"JSON report: {json_output}")
    print()
    print("This was a read-only comparison.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
