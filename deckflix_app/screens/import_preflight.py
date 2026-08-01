from deckflix_app.operation import (
    ImportPreflightResult,
)


def format_bytes(value: int) -> str:
    gib = value / 1024**3

    if gib >= 1024:
        return (
            f"{gib / 1024:.2f} TB"
        )

    return f"{gib:.2f} GB"


def print_check(
    passed: bool,
    description: str,
) -> None:
    symbol = "PASS" if passed else "FAIL"
    print(
        f"[{symbol}] {description}"
    )


def show_import_preflight(
    result: ImportPreflightResult,
    *,
    read_only: bool,
) -> None:
    print()
    print("Full Import Preflight")
    print("═════════════════════")
    print(
        "No files have been copied, moved, "
        "or deleted."
    )
    print()

    print("Operation")
    print("─────────")
    print(
        f"Approved files       "
        f"{result.approved_files}"
    )
    print(
        f"Approved data        "
        f"{format_bytes(result.approved_bytes)}"
    )
    print(
        f"Review items excluded "
        f"{result.review_items}"
    )
    print(
        f"Skipped items        "
        f"{result.skipped_items}"
    )

    print()
    print("Storage")
    print("───────")
    print(
        f"Movies required      "
        f"{format_bytes(result.movie_bytes)}"
    )
    print(
        f"Movies free          "
        f"{format_bytes(result.movie_free_bytes)}"
    )
    print(
        f"TV required          "
        f"{format_bytes(result.tv_bytes)}"
    )
    print(
        f"TV free              "
        f"{format_bytes(result.tv_free_bytes)}"
    )

    print()
    print("Checks")
    print("──────")

    print_check(
        result.snapshot_valid,
        "Shuttle snapshot is valid",
    )
    print_check(
        not result.missing_sources,
        "All approved source files exist",
    )
    print_check(
        not result.changed_sources,
        "Approved source files match snapshot",
    )
    print_check(
        not result.conflicts,
        "No destination files already exist",
    )
    print_check(
        result.movie_library_writable,
        "Movie library is writable",
    )
    print_check(
        result.tv_library_writable,
        "TV library is writable",
    )
    print_check(
        result.temp_writable,
        "Temporary directory is writable",
    )
    print_check(
        result.movie_free_bytes
        >= result.movie_bytes,
        "Movie library has enough free space",
    )
    print_check(
        result.tv_free_bytes
        >= result.tv_bytes,
        "TV library has enough free space",
    )

    print()
    print("Safe Mode")
    print("─────────")
    print(
        "Enabled"
        if read_only
        else "Disabled"
    )

    if result.errors:
        print()
        print("Blocking Reasons")
        print("────────────────")

        for error in result.errors:
            print(f"- {error}")

    if result.conflicts:
        print()
        print("Destination Conflicts")
        print("─────────────────────")

        for conflict in result.conflicts[:20]:
            print(
                f"- {conflict.destination}"
            )

        if len(result.conflicts) > 20:
            print(
                f"...and "
                f"{len(result.conflicts) - 20} "
                f"more conflicts."
            )

    if result.missing_sources:
        print()
        print("Missing Sources")
        print("───────────────")

        for source in result.missing_sources[:20]:
            print(f"- {source}")

    if result.changed_sources:
        print()
        print("Changed Sources")
        print("───────────────")

        for source in result.changed_sources[:20]:
            print(f"- {source}")

    print()
    print("Result")
    print("──────")

    if result.ready:
        print("FULL IMPORT READY")
    else:
        print("FULL IMPORT BLOCKED")

    if (
        result.ready
        and read_only
    ):
        print()
        print(
            "Preflight passed, but execution remains "
            "blocked by Safe Mode."
        )

    print()
    print("Nothing has been changed.")
