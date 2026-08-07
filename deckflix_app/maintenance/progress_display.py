from .progress import MaintenanceProgress


def format_bytes(value: float) -> str:
    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]

    size = float(value)

    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"

        size /= 1024

    return f"{size:.1f} PB"


def format_time(seconds: float) -> str:
    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (
        seconds % 3600
    ) // 60
    secs = seconds % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d}"
    )


def render_progress(
    progress: MaintenanceProgress,
):
    width = 30

    filled = int(
        width
        * progress.percent
        / 100
    )

    bar = (
        "█" * filled
        +
        "░" * (
            width - filled
        )
    )

    print("\033[2J\033[H", end="")

    print(
        "╔══════════════════════════════════════╗"
    )
    print(
        "║        DECKFLIX MAINTENANCE          ║"
    )
    print(
        "╚══════════════════════════════════════╝"
    )

    print()

    print(
        f"Stage:"
    )
    print(
        progress.stage
    )

    print()

    print(
        f"{bar} "
        f"{progress.percent:5.1f}%"
    )

    print()

    print(
        f"Files:"
        f" {progress.completed_files}"
        f" / {progress.total_files}"
    )

    print(
        f"Data:"
        f" {format_bytes(progress.completed_bytes)}"
        f" / {format_bytes(progress.total_bytes)}"
    )

    if progress.current_file:
        print()
        print(
            "Current:"
        )
        print(
            progress.current_file
        )

    print()

    print(
        "Speed:"
        f" {format_bytes(progress.bytes_per_second)}/s"
    )

    print(
        "Elapsed:"
        f" {format_time(progress.elapsed_seconds)}"
    )

    if progress.eta_seconds:
        print(
            "ETA:"
            f" {format_time(progress.eta_seconds)}"
        )
