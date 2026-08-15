from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess

from deckflix_app.shuttle_mount import (
    is_shuttle_mounted,
)

from .manager import OperationManager
from .shuttle_action import (
    run_shuttle_action_preflight,
)


@dataclass(frozen=True, slots=True)
class ShuttleMountIdentity:
    mount_path: Path
    source: str
    filesystem: str
    label: str


@dataclass(frozen=True, slots=True)
class ShuttleReleaseResult:
    emptied: bool
    unmounted: bool
    deleted_entries: int
    source: str
    filesystem: str
    label: str


def _run_command(
    args: list[str],
) -> str:
    completed = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )

    return completed.stdout.strip()


def inspect_shuttle_mount(
    shuttle_path: Path,
) -> ShuttleMountIdentity:
    path = Path(shuttle_path).resolve()

    if not is_shuttle_mounted(path):
        raise RuntimeError(
            "Shuttle is not a distinct mounted filesystem"
        )

    output = _run_command(
        [
            "findmnt",
            "-n",
            "-T",
            str(path),
            "-o",
            "TARGET,SOURCE,FSTYPE",
        ]
    )

    parts = output.split()

    if len(parts) < 3:
        raise RuntimeError(
            "Unable to determine shuttle mount identity"
        )

    target = Path(parts[0]).resolve()
    source = parts[1]
    filesystem = parts[2]

    if target != path:
        raise RuntimeError(
            "Mounted target does not match configured "
            f"shuttle path: {target}"
        )

    label = _run_command(
        [
            "lsblk",
            "-n",
            "-o",
            "LABEL",
            source,
        ]
    ).splitlines()

    volume_label = (
        label[0].strip()
        if label
        else ""
    )

    return ShuttleMountIdentity(
        mount_path=target,
        source=source,
        filesystem=filesystem,
        label=volume_label,
    )


def validate_release_identity(
    manager: OperationManager,
    *,
    expected_filesystem: str = "exfat",
    expected_label: str = "SHUTTLE",
) -> ShuttleMountIdentity:
    operation = manager.require_operation()
    snapshot = operation.snapshot

    mount = inspect_shuttle_mount(
        snapshot.shuttle_path
    )

    if (
        mount.filesystem.casefold()
        != expected_filesystem.casefold()
    ):
        raise RuntimeError(
            "Unexpected shuttle filesystem: "
            f"{mount.filesystem}"
        )

    if mount.label != expected_label:
        raise RuntimeError(
            "Unexpected shuttle volume label: "
            f"{mount.label!r}"
        )

    try:
        current_device_id = (
            mount.mount_path.stat().st_dev
        )
    except OSError as exc:
        raise RuntimeError(
            "Unable to read shuttle device identity"
        ) from exc

    if (
        current_device_id
        != snapshot.device_id
    ):
        raise RuntimeError(
            "Mounted shuttle device does not match "
            "the immutable operation snapshot"
        )

    return mount


def _delete_shuttle_contents(
    shuttle_path: Path,
) -> int:
    root = Path(shuttle_path).resolve()

    deleted_entries = 0

    for child in list(
        root.iterdir()
    ):
        if child.is_symlink():
            child.unlink()
            deleted_entries += 1
            continue

        if child.is_dir():
            shutil.rmtree(child)
            deleted_entries += 1
            continue

        child.unlink()
        deleted_entries += 1

    return deleted_entries


def execute_empty_and_unmount(
    manager: OperationManager,
    *,
    confirmation: str,
    expected_filesystem: str = "exfat",
    expected_label: str = "SHUTTLE",
) -> ShuttleReleaseResult:
    """
    Destructively empty the exact certified shuttle
    filesystem and then unmount it.

    This function deliberately requires the current
    operation ID as its confirmation token.

    It must not be exposed through the UI until its
    refusal paths have been fully tested.
    """
    operation = manager.require_operation()

    if confirmation != operation.id:
        raise RuntimeError(
            "Confirmation token does not match "
            "the active operation ID"
        )

    preflight = run_shuttle_action_preflight(
        manager
    )

    if not preflight.ready:
        reasons = "; ".join(
            preflight.reasons
        )

        raise RuntimeError(
            "Empty & Eject safety preflight blocked"
            + (
                f": {reasons}"
                if reasons
                else ""
            )
        )

    # Re-check mount/device/filesystem/label immediately
    # after the expensive safety preflight and before
    # the first destructive filesystem operation.
    mount = validate_release_identity(
        manager,
        expected_filesystem=expected_filesystem,
        expected_label=expected_label,
    )

    shuttle_root = (
        operation.snapshot.shuttle_path.resolve()
    )

    if shuttle_root != mount.mount_path:
        raise RuntimeError(
            "Shuttle mount changed before deletion"
        )

    deleted_entries = (
        _delete_shuttle_contents(
            shuttle_root
        )
    )

    remaining = list(
        shuttle_root.iterdir()
    )

    if remaining:
        raise RuntimeError(
            "Shuttle deletion verification failed: "
            f"{len(remaining)} top-level entries remain"
        )

    # Flush all pending filesystem writes before
    # attempting to unmount.
    os.sync()

    _run_command(
        [
            "sudo",
            "umount",
            str(shuttle_root),
        ]
    )

    if is_shuttle_mounted(
        shuttle_root
    ):
        raise RuntimeError(
            "Shuttle still appears mounted after umount"
        )

    return ShuttleReleaseResult(
        emptied=True,
        unmounted=True,
        deleted_entries=deleted_entries,
        source=mount.source,
        filesystem=mount.filesystem,
        label=mount.label,
    )


def execute_unmount_only(
    manager: OperationManager,
    *,
    expected_filesystem: str = "exfat",
    expected_label: str = "SHUTTLE",
) -> ShuttleReleaseResult:
    """
    Safely unmount the current operation shuttle
    without deleting any shuttle contents.

    Final Safety Validation is deliberately not
    required because Eject Only is non-destructive.
    """
    operation = manager.require_operation()

    manager.require_valid_snapshot()

    mount = validate_release_identity(
        manager,
        expected_filesystem=expected_filesystem,
        expected_label=expected_label,
    )

    shuttle_root = (
        operation.snapshot
        .shuttle_path
        .resolve()
    )

    if shuttle_root != mount.mount_path:
        raise RuntimeError(
            "Shuttle mount changed before unmount"
        )

    os.sync()

    _run_command(
        [
            "sudo",
            "umount",
            str(shuttle_root),
        ]
    )

    if is_shuttle_mounted(
        shuttle_root
    ):
        raise RuntimeError(
            "Shuttle still appears mounted after umount"
        )

    return ShuttleReleaseResult(
        emptied=False,
        unmounted=True,
        deleted_entries=0,
        source=mount.source,
        filesystem=mount.filesystem,
        label=mount.label,
    )
