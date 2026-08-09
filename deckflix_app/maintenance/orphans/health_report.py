from pathlib import Path

from .health import generate_health_report


def show_health_report(
    source: Path,
    destination: Path,
) -> None:

    report = generate_health_report(
        source,
        destination,
    )

    print()

    print(
        "DECKFLIX MEDIA HEALTH"
    )

    print(
        "═════════════════════"
    )

    print()

    print(
        "CLASSIFICATION"
    )

    print(
        "──────────────"
    )

    print(
        f"Migration leftovers : "
        f"{report.migration_leftovers}"
    )

    print(
        f"Release junk        : "
        f"{report.release_junk}"
    )

    print(
        f"Collection folders  : "
        f"{report.collection_containers}"
    )

    print(
        f"Manual review       : "
        f"{report.orphan_movies}"
    )

    print()

    print(
        "QUALITY ANALYSIS"
    )

    print(
        "────────────────"
    )

    print(
        f"Duplicate media     : "
        f"{report.duplicate_media}"
    )

    print(
        f"Source better       : "
        f"{report.source_better}"
    )

    print(
        f"Quality review      : "
        f"{report.quality_review}"
    )

    print()

    print(
        "CLEANUP"
    )

    print(
        "───────"
    )

    print(
        f"Approved actions    : "
        f"{report.cleanup_actions}"
    )

    print()
