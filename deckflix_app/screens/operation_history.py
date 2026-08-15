from datetime import datetime
from pathlib import Path

from deckflix_app.operation import (
    list_history_records,
    list_repair_history_records,
)


def format_bytes(value: int) -> str:
    gib = value / 1024**3

    if gib >= 1024:
        return f"{gib / 1024:.2f} TB"

    return f"{gib:.2f} GB"


def format_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)

        return parsed.strftime(
            "%Y-%m-%d %H:%M"
        )
    except ValueError:
        return value


def _show_import_history(
    history_directory: Path,
    *,
    limit: int = 30,
) -> None:
    print()
    print("Import Operation History")
    print("═════════════════════════")

    records = list_history_records(
        Path(history_directory)
    )

    if not records:
        print()
        print(
            "No completed import operations recorded."
        )

        input(
            "\nPress Enter to continue..."
        )

        return

    print()
    print(
        f"{'Completed':<18} "
        f"{'Operation':<30} "
        f"{'Imported':>8} "
        f"{'Failed':>6} "
        f"{'Status':<16}"
    )

    print("─" * 86)

    for record in records[:limit]:
        status = (
            "SAFE TO EMPTY"
            if record.safe_to_empty
            else "NOT SAFE"
        )

        print(
            f"{format_timestamp(record.completed_at):<18} "
            f"{record.operation_id:<30} "
            f"{record.imported:>8} "
            f"{record.failed:>6} "
            f"{status:<16}"
        )

    print()
    print(
        f"History directory: "
        f"{history_directory}"
    )

    input(
        "\nPress Enter to continue..."
    )


def _show_repair_history_detail(
    record,
) -> None:
    print()
    print("Repair Operation")
    print("════════════════")

    print()
    print(
        f"Operation ID       "
        f"{record.operation_id}"
    )

    print(
        f"Created            "
        f"{format_timestamp(record.created_at)}"
    )

    print(
        f"Completed          "
        f"{format_timestamp(record.updated_at)}"
    )

    print(
        f"State              "
        f"{record.state}"
    )

    print(
        f"Write authorization "
        f"{'ENABLED' if record.write_authorized else 'REVOKED'}"
    )

    print()
    print(
        f"Approved repairs   "
        f"{record.entries}"
    )

    print(
        f"Verified           "
        f"{record.verified}"
    )

    print(
        f"Failed             "
        f"{record.failed}"
    )

    print(
        f"Pending            "
        f"{record.pending}"
    )

    print(
        f"Copying            "
        f"{record.copying}"
    )

    print(
        f"Total size         "
        f"{format_bytes(record.total_bytes)}"
    )

    print()
    print("Repair Results")
    print("──────────────")

    for number, entry in enumerate(
        record.entries_detail,
        start=1,
    ):
        print()
        print(
            f"{number:02d}  "
            f"{entry.status}"
        )

        print(
            f"    FROM: {entry.source}"
        )

        print(
            f"    TO:   {entry.destination}"
        )

        print(
            f"    Action: {entry.action}"
        )

        print(
            f"    Reason: {entry.reason}"
        )

        print(
            f"    Size: "
            f"{format_bytes(entry.source_size)}"
        )

        if entry.source_checksum:
            print(
                f"    Source SHA-256:      "
                f"{entry.source_checksum}"
            )

        if entry.destination_checksum:
            print(
                f"    Destination SHA-256: "
                f"{entry.destination_checksum}"
            )

        if entry.completed_at:
            print(
                f"    Completed: "
                f"{format_timestamp(entry.completed_at)}"
            )

        if entry.error:
            print(
                f"    ERROR: "
                f"{entry.error}"
            )

        if (
            entry.destination_checksum
            and entry.source_checksum
        ):
            if (
                entry.destination_checksum
                == entry.source_checksum
            ):
                print(
                    "    SHA-256 verification: MATCH"
                )
            else:
                print(
                    "    SHA-256 verification: MISMATCH"
                )

    print()
    print(
        "HISTORICAL RECORD — READ ONLY"
    )

    print(
        "This operation cannot be executed "
        "from history."
    )

    input(
        "\nPress Enter to continue..."
    )


def _show_repair_history(
    history_directory: Path,
    *,
    limit: int = 30,
) -> None:
    print()
    print("Repair Operation History")
    print("═════════════════════════")

    records = list_repair_history_records(
        Path(history_directory)
    )

    if not records:
        print()
        print(
            "No completed repair operations recorded."
        )

        input(
            "\nPress Enter to continue..."
        )

        return

    print()
    print(
        f"{'Completed':<18} "
        f"{'Operation':<30} "
        f"{'Files':>7} "
        f"{'Verified':>9} "
        f"{'Failed':>7} "
        f"{'State':<12}"
    )

    print("─" * 96)

    for number, record in enumerate(
        records[:limit],
        start=1,
    ):
        print(
            f"{number:>2}. "
            f"{format_timestamp(record.updated_at):<15} "
            f"{record.operation_id:<30} "
            f"{record.entries:>7} "
            f"{record.verified:>9} "
            f"{record.failed:>7} "
            f"{record.state:<12}"
        )

    print()
    print(
        f"History directory: "
        f"{history_directory}"
    )

    print()
    print(
        "Select operation number, "
        "or press Enter to go back."
    )

    choice = input(
        "Select: "
    ).strip()

    if not choice:
        return

    try:
        number = int(choice)
    except ValueError:
        print("Invalid option.")

        input(
            "\nPress Enter to continue..."
        )

        return

    visible_records = records[:limit]

    if (
        number < 1
        or number > len(visible_records)
    ):
        print(
            "Invalid operation number."
        )

        input(
            "\nPress Enter to continue..."
        )

        return

    _show_repair_history_detail(
        visible_records[number - 1]
    )


def show_operation_history(
    history_directory: Path,
    *,
    limit: int = 30,
) -> None:
    history_directory = Path(
        history_directory
    )

    repair_history_directory = (
        history_directory.parent
        / "repair-history"
    )

    while True:
        print()
        print("Operation History")
        print("═════════════════")
        print()
        print("1. Import Operations")
        print("2. Repair Operations")
        print("3. Back")
        print()

        choice = input(
            "Select option: "
        ).strip()

        if choice == "1":
            _show_import_history(
                history_directory,
                limit=limit,
            )

            continue

        if choice == "2":
            _show_repair_history(
                repair_history_directory,
                limit=limit,
            )

            continue

        if choice == "3":
            return

        print("Invalid option.")
