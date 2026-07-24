import json
import subprocess
from pathlib import Path

from deckflix_app.config.config import (
    CONFIG_FILE,
    get_enabled_libraries,
    get_quarantine_path,
    get_shuttle_path,
)
from deckflix_app.library_manager import get_all_library_statuses


def check_configuration():
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            config = json.load(file)

        return {
            "name": "Configuration",
            "success": True,
            "message": f"Valid — version {config.get('version', 'unknown')}",
        }
    except (OSError, json.JSONDecodeError) as error:
        return {
            "name": "Configuration",
            "success": False,
            "message": str(error),
        }


def check_libraries():
    checks = []

    for status in get_all_library_statuses():
        if status["online"]:
            message = (
                f"Online — {status['used_percent']:.1f}% used, "
                f"{status['free_bytes'] / 1024**4:.2f} TiB free"
            )
        else:
            message = f"Offline — {status['path']}"

        checks.append(
            {
                "name": status["name"],
                "success": status["online"],
                "message": message,
            }
        )

    configured_names = {
        library["name"]
        for library in get_enabled_libraries()
    }

    if not configured_names:
        checks.append(
            {
                "name": "Libraries",
                "success": False,
                "message": "No enabled libraries configured.",
            }
        )

    return checks


def check_shuttle():
    path = get_shuttle_path()
    connected = path.exists() and path.is_dir()

    return {
        "name": "Shuttle",
        "success": connected,
        "message": f"Connected — {path}" if connected else f"Not found — {path}",
    }


def check_quarantine():
    path = get_quarantine_path()

    try:
        path.mkdir(parents=True, exist_ok=True)
        available = path.exists() and path.is_dir()
    except OSError:
        available = False

    return {
        "name": "Quarantine",
        "success": available,
        "message": f"Available — {path}" if available else f"Unavailable — {path}",
    }


def check_jellyfin():
    try:
        result = subprocess.run(
            [
                "pct",
                "exec",
                "100",
                "--",
                "systemctl",
                "is-active",
                "jellyfin",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        active = result.returncode == 0 and result.stdout.strip() == "active"

        return {
            "name": "Jellyfin",
            "success": active,
            "message": "Running" if active else "Not running",
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return {
            "name": "Jellyfin",
            "success": False,
            "message": str(error),
        }


def run_doctor():
    checks = [
        check_configuration(),
        *check_libraries(),
        check_shuttle(),
        check_quarantine(),
        check_jellyfin(),
    ]

    print()
    print("DeckFlix Doctor")
    print("═══════════════")
    print()

    for check in checks:
        symbol = "✓" if check["success"] else "✗"
        print(f"{symbol} {check['name']:<16} {check['message']}")

    healthy = all(check["success"] for check in checks)

    print()
    print("Overall")
    print("───────")
    print("✓ System healthy" if healthy else "✗ Attention required")
    print()

    return healthy
