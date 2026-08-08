from pathlib import Path

from .scanner import scan_orphans
from .report import print_orphan_report


def show_orphan_review(
    source: Path,
    destination: Path,
):

    results = scan_orphans(
        source,
        destination,
    )

    print_orphan_report(
        results
    )

    print()

    print(
        "[B] Back"
    )

    input(
        "Press Enter to continue..."
    )
