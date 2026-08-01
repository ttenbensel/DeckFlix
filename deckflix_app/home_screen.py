from pathlib import Path


def path_status(path: Path) -> str:
    return "ONLINE" if path.exists() else "OFFLINE"


def mode_name(read_only: bool) -> str:
    return "SAFE MODE" if read_only else "IMPORT MODE"


def show_home_screen(
    *,
    app_name: str,
    version: str,
    codename: str,
    config,
) -> None:
    shuttle = Path(config.shuttle)
    movie_libraries = [Path(path) for path in config.movie_libraries]
    tv_libraries = [Path(path) for path in config.tv_libraries]
    libraries = movie_libraries + tv_libraries

    online_libraries = sum(
        1 for path in libraries if path.exists()
    )

    shuttle_connected = shuttle.exists()
    shuttle_label = shuttle.name.upper()

    print("╔══════════════════════════════════════════════════════════════╗")
    print(f"║ {app_name.upper():^60} ║")
    print("║ Shipboard Media Management System".ljust(63) + "║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print()

    print(
        f" Shuttle     "
        f"{'● Connected' if shuttle_connected else '○ Not Connected':<16} "
        f"{shuttle_label}"
    )

    print(
        f" Libraries   "
        f"{'● Online' if online_libraries == len(libraries) else '○ Degraded':<16} "
        f"{online_libraries}/{len(libraries)}"
    )

    print(
        f" Mode        "
        f"{'● ' + mode_name(config.read_only)}"
    )

    print(
        f" Profile     "
        f"{config.operating_profile}"
    )

    print(
        f" Low Impact  "
        f"{'● Enabled' if config.low_impact else '○ Disabled'}"
    )

    print()
    print("──────────────────────────────────────────────────────────────")
    print(f" Version {version} — {codename}")
    print("══════════════════════════════════════════════════════════════")
    print()
