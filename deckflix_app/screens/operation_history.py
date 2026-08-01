from datetime import datetime
from pathlib import Path

from deckflix_app.operation import list_history_records


def format_bytes(value: int) -> str:
    gib = value / 1024**3

    if gib >= 1024:
        return f"{gib / 1024:.2f} TB"

    return f"{gib:.2f} GB"


def format_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def show_operation_history(
    history_directory: Path,
    *,
    limit: int = 30,
) -> None:
    print()
    print("Operation History")
    print("═════════════════")

    records = list_history_records(
        Path(history_directory)
    )

    if not records:
        print()
        print("No completed operations recorded.")
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
    print(f"History directory: {history_directory}")
