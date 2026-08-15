from pathlib import Path

from deckflix_app.shuttle_mount import (
    is_shuttle_mounted,
)

from deckflix_app.decision import ApprovalStatus
from deckflix_app.operation import OperationManager, OperationState
from deckflix_app.operating_modes import infer_operating_mode


def path_status(path: Path) -> str:
    return "ONLINE" if path.exists() else "OFFLINE"


def recommended_action(
    manager: OperationManager | None,
    *,
    read_only: bool,
) -> str:
    if manager is None or not manager.active:
        return "Begin Shuttle Operation"

    state = manager.state

    if state is OperationState.INVALIDATED:
        return "Clear Operation and Re-analyse Shuttle"

    if state is OperationState.SNAPSHOT_READY:
        plan = manager.approval_plan

        if plan is None:
            return "Build Approval Plan"

        ready = plan.count(ApprovalStatus.READY)
        review = plan.count(ApprovalStatus.REVIEW)

        if ready:
            return f"Review and Approve {ready} Ready Import(s)"

        if review:
            return f"Resolve {review} Review Item(s)"

        return "Review Operation"

    if state is OperationState.APPROVED:
        if manager.import_authorized:
            return "Execute Approved Import"

        if read_only:
            return "Enable Import Mode"

        return "Execute Approved Import"

    if state is OperationState.IMPORTING:
        return "Monitor Active Import"

    if state is OperationState.COMPLETE:
        certificate = manager.certificate

        if (
            certificate is not None
            and certificate.safety.safe
        ):
            return "Review Certificate — Safe to Empty"

        return "Review Completed Operation"

    return "Review Operation Dashboard"


def show_operation_summary(
    manager: OperationManager | None,
    *,
    read_only: bool,
) -> None:
    print()
    print("Current Operation")
    print("─────────────────")

    if manager is None or not manager.active:
        print(" Status      No active operation")
        print(" Next Action Begin Shuttle Operation")
        return

    operation = manager.require_operation()
    snapshot = operation.snapshot

    snapshot_valid = manager.validate_snapshot()

    print(f" ID          {operation.id}")
    print(f" State       {manager.state.value}")
    print(
        f" Snapshot    "
        f"{'VALID' if snapshot_valid else 'INVALID'}"
    )
    print(f" Files       {snapshot.file_count}")

    if manager.approval_plan is not None:
        plan = manager.approval_plan

        print(
            f" Ready       "
            f"{plan.count(ApprovalStatus.READY)}"
        )
        print(
            f" Approved    "
            f"{plan.count(ApprovalStatus.APPROVED)}"
        )
        print(
            f" Review      "
            f"{plan.count(ApprovalStatus.REVIEW)}"
        )

    print()
    print("Recommended Next Action")
    print("───────────────────────")
    print(
        f" ▶ {recommended_action(manager, read_only=read_only)}"
    )


def show_home_screen(
    *,
    app_name: str,
    version: str,
    codename: str,
    config,
    operation_manager: OperationManager | None = None,
) -> None:
    shuttle = Path(config.shuttle)

    movie_libraries = [
        Path(path)
        for path in config.movie_libraries
    ]
    tv_libraries = [
        Path(path)
        for path in config.tv_libraries
    ]
    libraries = movie_libraries + tv_libraries

    online_libraries = sum(
        1
        for path in libraries
        if path.exists()
    )

    shuttle_connected = is_shuttle_mounted(
        shuttle
    )
    shuttle_label = shuttle.name.upper()

    print(
        "╔════════════════════════════════════════════════"
        "══════════════╗"
    )
    print(f"║ {app_name.upper():^60} ║")
    print(
        "║ Shipboard Media Management System".ljust(63)
        + "║"
    )
    print(
        "╠════════════════════════════════════════════════"
        "══════════════╣"
    )
    print()

    print(
        f" Shuttle     "
        f"{'● Connected' if shuttle_connected else '○ Not Connected':<16} "
        f"{shuttle_label}"
    )

    libraries_status = (
        "● Online"
        if online_libraries == len(libraries)
        else "○ Degraded"
    )

    print(
        f" Libraries   "
        f"{libraries_status:<16} "
        f"{online_libraries}/{len(libraries)}"
    )

    operating_mode = infer_operating_mode(config)

    show_operation_summary(
        operation_manager,
        read_only=config.read_only,
    )

    print()
    print("System Status")
    print("─────────────")

    print(
        f" Operating Mode      "
        f"{operating_mode.display_name}"
    )

    print(
        f" Network             "
        f"{operating_mode.connectivity}"
    )

    print(
        f" Library Protection  "
        f"{'🔒 Enabled' if config.read_only else '🔓 Off'}"
    )

    print(
        f" Low Impact          "
        f"{'● Enabled' if config.low_impact else '○ Off'}"
    )

    print(
        f"                     "
        f"{operating_mode.motto}"
    )

    print()
    print(
        "────────────────────────────────────────────────"
        "──────────────"
    )
    print(f" Version {version} — {codename}")
    print(
        "════════════════════════════════════════════════"
        "══════════════"
    )
    print()
