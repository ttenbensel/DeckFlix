from pathlib import Path


def is_shuttle_mounted(
    shuttle_path: Path,
) -> bool:
    """
    Return True only when the configured shuttle path
    represents a distinct mounted filesystem.

    An existing empty mount directory on the root
    filesystem must never count as a connected shuttle.
    """
    path = Path(shuttle_path)

    try:
        if not path.exists():
            return False

        if not path.is_dir():
            return False

        if not path.is_mount():
            return False

        parent = path.parent

        if path.stat().st_dev == parent.stat().st_dev:
            return False

    except OSError:
        return False

    return True


def require_shuttle_mounted(
    shuttle_path: Path,
) -> Path:
    """
    Return the resolved shuttle path or fail closed when
    no distinct shuttle filesystem is mounted there.
    """
    path = Path(shuttle_path).resolve()

    if not is_shuttle_mounted(path):
        raise RuntimeError(
            "Shuttle is not mounted at "
            f"{path}. Refusing to use the mount "
            "directory as shuttle storage."
        )

    return path
