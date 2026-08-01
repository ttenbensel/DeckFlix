from pathlib import Path

from deckflix_app.decision import (
    Action,
    DecisionQueueItem,
    build_decision_queue_from_paths,
)


ACTION_LABELS = {
    Action.NEW: "IMPORT",
    Action.UPGRADE: "UPGRADE",
    Action.DUPLICATE: "SKIP",
    Action.DOWNGRADE: "KEEP EXISTING",
    Action.BELOW_TARGET: "REVIEW",
    Action.REVIEW: "REVIEW",
}


def media_name(item: DecisionQueueItem) -> str:
    media = item.incoming

    if media.media_type == "tv":
        return (
            f"{media.title} "
            f"S{media.season:02d}E{media.episode:02d}"
        )

    if media.year:
        return f"{media.title} ({media.year})"

    return media.title


def show_decision_queue(
    *,
    shuttle_path: Path,
    movie_libraries: list[Path],
    tv_libraries: list[Path],
    sample_limit: int = 40,
) -> None:
    print()
    print("Decision Queue")
    print("══════════════")
    print("Read-only analysis. Nothing will be imported or changed.")
    print()
    print("Scanning shuttle and libraries...")

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

    summary = queue.summary()

    print()
    print("Summary")
    print("───────")
    print(f"Files analysed      {queue.total}")
    print(f"Import new          {summary[Action.NEW]}")
    print(f"Quality upgrades    {summary[Action.UPGRADE]}")
    print(f"Equivalent copies   {summary[Action.DUPLICATE]}")
    print(f"Keep existing       {summary[Action.DOWNGRADE]}")
    print(f"Needs review        {summary[Action.REVIEW]}")
    print()

    print("Decisions")
    print("─────────")

    if not queue.items:
        print("No shuttle media found.")
        return

    for index, item in enumerate(
        queue.items[:sample_limit],
        start=1,
    ):
        decision = item.decision
        label = ACTION_LABELS[decision.action]

        print(f"{index:2}. [{label}] {media_name(item)}")
        print(f"    Reason   : {decision.reason}")
        print(
            f"    Incoming : {decision.incoming_score}"
        )

        if item.existing is not None:
            print(
                f"    Existing : {decision.existing_score}"
            )

        print(
            f"    Confidence: {decision.confidence}%"
        )
        print()

    remaining = queue.total - sample_limit

    if remaining > 0:
        print(f"...and {remaining} more decisions.")

    print()
    print("Nothing has been changed.")


def show_managed_decision_queue(manager) -> None:
    print()
    print("Decision Queue")
    print("══════════════")

    if not manager.active:
        print()
        print("No operation is active.")
        print("Begin a shuttle operation first.")
        return

    if manager.decisions is None:
        print()
        print("The active operation has no decisions.")
        return

    queue = manager.decisions
    summary = queue.summary()

    print()
    print(f"Operation           {manager.operation.id}")
    print(f"Files analysed      {queue.total}")
    print(f"Import new          {summary[Action.NEW]}")
    print(f"Quality upgrades    {summary[Action.UPGRADE]}")
    print(f"Equivalent copies   {summary[Action.DUPLICATE]}")
    print(f"Keep existing       {summary[Action.DOWNGRADE]}")
    print(f"Needs review        {summary[Action.REVIEW]}")
    print()

    for index, item in enumerate(queue.items[:40], start=1):
        decision = item.decision

        print(
            f"{index:2}. "
            f"[{ACTION_LABELS[decision.action]}] "
            f"{media_name(item)}"
        )
        print(f"    Reason: {decision.reason}")
        print()

    if queue.total > 40:
        print(f"...and {queue.total - 40} more decisions.")

    print()
    print("Nothing has been changed.")
