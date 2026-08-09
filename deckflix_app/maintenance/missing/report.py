from pathlib import Path

from .scanner import scan_missing_episodes


def print_missing_report(
    library: Path,
):

    results = scan_missing_episodes(
        library
    )


    print()

    print(
        "DECKFLIX MISSING MEDIA"
    )

    print(
        "══════════════════════"
    )

    print()

    print(
        "EPISODE GAPS"
    )

    print(
        "─────────────"
    )


    if not results:

        print(
            "No missing episodes detected"
        )

    else:

        for item in results:

            print(
                f"{item.show}"
                f" S{item.season:02d}"
                f"E{item.episode:02d}"
            )

            print(
                f"  {item.reason}"
            )
