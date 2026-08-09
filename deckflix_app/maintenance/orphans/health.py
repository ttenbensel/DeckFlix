from dataclasses import dataclass
from pathlib import Path
from collections import Counter

from .scanner import scan_orphans
from .planner import create_orphan_cleanup_plan
from .duplicate_scanner import scan_duplicates


@dataclass(slots=True)
class MediaHealthReport:
    migration_leftovers: int
    release_junk: int
    collection_containers: int
    orphan_movies: int

    duplicate_media: int
    source_better: int
    quality_review: int

    cleanup_actions: int


def generate_health_report(
    source: Path,
    destination: Path,
) -> MediaHealthReport:

    results = scan_orphans(
        source,
        destination,
    )


    counts = Counter(
        item.classification.value
        for item in results
    )


    cleanup_plan = create_orphan_cleanup_plan(
        results
    )


    duplicates = scan_duplicates(
        source,
        destination,
    )


    duplicate_counts = Counter(
        item.classification.value
        for item in duplicates
    )


    return MediaHealthReport(
        migration_leftovers=counts.get(
            "MIGRATION_LEFTOVER",
            0,
        ),

        release_junk=counts.get(
            "RELEASE_JUNK",
            0,
        ),

        collection_containers=counts.get(
            "COLLECTION_CONTAINER",
            0,
        ),

        orphan_movies=counts.get(
            "ORPHAN_MOVIE",
            0,
        ),


        duplicate_media=duplicate_counts.get(
            "DUPLICATE_MEDIA",
            0,
        ),

        source_better=duplicate_counts.get(
            "SOURCE_BETTER",
            0,
        ),

        quality_review=duplicate_counts.get(
            "QUALITY_REVIEW",
            0,
        ),


        cleanup_actions=cleanup_plan.total_actions,
    )
