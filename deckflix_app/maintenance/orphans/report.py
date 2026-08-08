from collections import Counter

from .models import OrphanCandidate


def print_orphan_report(
    results: list[OrphanCandidate],
):
    counts = Counter(
        item.classification.value
        for item in results
    )

    print()

    print(
        "DECKFLIX MEDIA HEALTH REVIEW"
    )

    print(
        "═══════════════════════════"
    )

    print()

    print(
        f"Migration leftovers : "
        f"{counts.get('MIGRATION_LEFTOVER', 0)}"
    )

    print(
        f"Release junk        : "
        f"{counts.get('RELEASE_JUNK', 0)}"
    )

    print(
        f"Orphan movies       : "
        f"{counts.get('ORPHAN_MOVIE', 0)}"
    )

    print()

    print(
        "Examples"
    )

    print(
        "────────"
    )

    for item in results[:20]:

        print()

        print(
            item.classification.value
        )

        print(
            item.path
        )

        print(
            item.reason
        )
