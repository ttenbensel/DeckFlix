from deckflix_app.decision import ApprovalStatus
from deckflix_app.operation import OperationManager


def format_bytes(value: int) -> str:
    gib = value / 1024**3

    if gib >= 1024:
        return f"{gib / 1024:.2f} TB"

    return f"{gib:.2f} GB"


def show_operation_dashboard(
    manager: OperationManager,
) -> None:
    print()
    print("Operation Dashboard")
    print("═══════════════════")

    if not manager.active:
        print()
        print("No operation is active.")
        print("Begin a shuttle operation first.")
        return

    operation = manager.require_operation()
    snapshot = operation.snapshot
    snapshot_valid = manager.validate_snapshot()

    print()
    print("Operation")
    print("─────────")
    print(f"ID                 {operation.id}")
    print(f"State              {manager.state.value}")
    print(
        f"Created            "
        f"{operation.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print()
    print("Shuttle Snapshot")
    print("────────────────")
    print(f"Path               {snapshot.shuttle_path}")
    print(f"Files              {snapshot.file_count}")
    print(f"Media size         {format_bytes(snapshot.total_bytes)}")
    print(
        f"Fingerprint        "
        f"{snapshot.fingerprint[:16]}..."
    )
    print(
        f"Snapshot status    "
        f"{'VALID' if snapshot_valid else 'INVALID'}"
    )

    if manager.decisions is not None:
        print()
        print("Decision Queue")
        print("──────────────")
        print(f"Total              {manager.decisions.total}")

    if manager.approval_plan is not None:
        plan = manager.approval_plan

        print()
        print("Approval Plan")
        print("─────────────")
        print(
            f"Ready              "
            f"{plan.count(ApprovalStatus.READY)}"
        )
        print(
            f"Approved           "
            f"{plan.count(ApprovalStatus.APPROVED)}"
        )
        print(
            f"Skipped            "
            f"{plan.count(ApprovalStatus.SKIPPED)}"
        )
        print(
            f"Review             "
            f"{plan.count(ApprovalStatus.REVIEW)}"
        )

    print()
    print("No files have been changed.")
