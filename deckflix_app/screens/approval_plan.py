from pathlib import Path

from deckflix_app.decision import (
    Action,
    ApprovalStatus,
    build_approval_plan,
    build_decision_queue_from_paths,
)


ACTION_LABELS = {
    Action.NEW: "IMPORT",
    Action.UPGRADE: "UPGRADE",
    Action.DUPLICATE: "DUPLICATE",
    Action.DOWNGRADE: "DOWNGRADE",
    Action.BELOW_TARGET: "BELOW TARGET",
    Action.REVIEW: "REVIEW",
}


def media_name(item) -> str:
    media = item.queue_item.incoming

    if media.media_type == "tv":
        return (
            f"{media.title} "
            f"S{media.season:02d}E{media.episode:02d}"
        )

    if media.year:
        return f"{media.title} ({media.year})"

    return media.title


def show_approval_plan(
    *,
    shuttle_path: Path,
    movie_libraries: list[Path],
    tv_libraries: list[Path],
    sample_limit: int = 40,
) -> None:
    print()
    print("Decision Approval")
    print("═════════════════")
    print("Read-only preview. No files will be imported or changed.")
    print()
    print("Building decision and approval plans...")

    queue = build_decision_queue_from_paths(
        shuttle_path=Path(shuttle_path),
        movie_libraries=[
            Path(path)
            for path in movie_libraries
        ],
        tv_libraries=[
            Path(path)
            for path in tv_libraries
        ],
    )

    plan = build_approval_plan(queue)

    print()
    print("Approval Summary")
    print("────────────────")
    print(f"Total decisions     {plan.total}")
    print(
        f"Ready to approve    "
        f"{plan.count(ApprovalStatus.READY)}"
    )
    print(
        f"Operator approved   "
        f"{plan.count(ApprovalStatus.APPROVED)}"
    )
    print(
        f"Skipped             "
        f"{plan.count(ApprovalStatus.SKIPPED)}"
    )
    print(
        f"Needs review        "
        f"{plan.count(ApprovalStatus.REVIEW)}"
    )

    print()
    print("Approval Preview")
    print("────────────────")

    if not plan.items:
        print("No decisions available.")
        return

    for index, item in enumerate(
        plan.items[:sample_limit],
        start=1,
    ):
        decision = item.queue_item.decision
        action = ACTION_LABELS[decision.action]

        print(
            f"{index:2}. "
            f"[{item.status.value}] "
            f"[{action}] "
            f"{media_name(item)}"
        )
        print(f"    Reason: {decision.reason}")

        if item.status is ApprovalStatus.REVIEW:
            print("    Operator approval required")

        print()

    remaining = plan.total - sample_limit

    if remaining > 0:
        print(f"...and {remaining} more approval items.")

    print()
    print("READY means proposed only.")
    print("No operator approval has been saved.")
    print("Nothing has been changed.")


def show_managed_approval_plan(manager) -> None:
    print()
    print("Decision Approval")
    print("═════════════════")

    if not manager.active:
        print()
        print("No operation is active.")
        print("Begin a shuttle operation first.")
        return

    if manager.approval_plan is None:
        print()
        print("The active operation has no approval plan.")
        return

    plan = manager.approval_plan

    print()
    print(f"Operation           {manager.operation.id}")
    print(f"Total decisions     {plan.total}")
    print(
        f"Ready to approve    "
        f"{plan.count(ApprovalStatus.READY)}"
    )
    print(
        f"Operator approved   "
        f"{plan.count(ApprovalStatus.APPROVED)}"
    )
    print(
        f"Skipped             "
        f"{plan.count(ApprovalStatus.SKIPPED)}"
    )
    print(
        f"Needs review        "
        f"{plan.count(ApprovalStatus.REVIEW)}"
    )
    print()

    for index, item in enumerate(plan.items[:40], start=1):
        decision = item.queue_item.decision

        print(
            f"{index:2}. "
            f"[{item.status.value}] "
            f"[{ACTION_LABELS[decision.action]}] "
            f"{media_name(item)}"
        )
        print(f"    Reason: {decision.reason}")
        print()

    if plan.total > 40:
        print(f"...and {plan.total - 40} more items.")

    print()
    print("Nothing has been changed.")
