from collections import defaultdict
from pathlib import Path

from deckflix_app.decision import (
    build_approval_plan,
    build_decision_queue_from_paths,
)
from deckflix_app.library.index import media_key
from deckflix_app.scanner import metadata_from_file

from .manager import OperationManager
from .models import Operation


def account_superseded_snapshot_files(
    manager: OperationManager,
) -> int:
    """
    Account for physical shuttle files intentionally collapsed by
    verified incoming logical deduplication.

    The decision queue operates on one winning physical candidate
    per complete logical media identity. The immutable shuttle
    snapshot, however, records every physical media file.

    Any snapshot path absent from the decision queue is marked
    SUPERSEDED only when it can be mapped exactly to a surviving
    queue item's logical media key.

    A missing path with no surviving logical identity is deliberately
    left UNRESOLVED. This method never invents evidence and never
    widens the set of accounted files merely to satisfy coverage.

    No filesystem changes are performed.
    """
    operation = manager.require_operation()
    decisions = manager.decisions

    if decisions is None:
        raise RuntimeError(
            "Decision queue is required before "
            "superseded snapshot accounting"
        )

    ledger = manager.require_ledger()

    shuttle_root = (
        operation.snapshot.shuttle_path
        .resolve()
    )

    surviving_paths: set[Path] = set()

    survivors_by_key = defaultdict(list)

    for item in decisions.items:
        incoming = item.incoming

        if incoming.path is None:
            continue

        survivor_path = (
            Path(incoming.path).resolve()
        )

        try:
            survivor_path.relative_to(
                shuttle_root
            )
        except ValueError:
            raise RuntimeError(
                "Decision source is outside the "
                f"operation shuttle: {survivor_path}"
            )

        surviving_paths.add(
            survivor_path
        )

        survivors_by_key[
            media_key(incoming)
        ].append(
            survivor_path
        )

    accounted = 0

    for snapshot_file in operation.snapshot.files:
        absolute = (
            shuttle_root
            / snapshot_file.relative_path
        ).resolve()

        if absolute in surviving_paths:
            continue

        media = metadata_from_file(
            absolute
        )

        key = media_key(
            media
        )

        survivors = survivors_by_key.get(
            key,
            [],
        )

        if not survivors:
            # Fail closed. The snapshot entry remains UNRESOLVED.
            continue

        # Verified queue construction chooses one representative for
        # a logical identity. If a future queue shape ever exposes
        # more than one surviving representative, do not guess.
        if len(survivors) != 1:
            continue

        survivor = survivors[0]

        if survivor == absolute:
            continue

        ledger.mark_superseded(
            snapshot_file.relative_path,
            surviving_path=survivor,
            detail=(
                "Physical shuttle candidate was suppressed by "
                "verified logical incoming deduplication"
            ),
        )

        accounted += 1

    return accounted


def prepare_operation(
    manager: OperationManager,
    *,
    shuttle_path: Path,
    movie_libraries: list[Path],
    tv_libraries: list[Path],
    operation_id: str | None = None,
) -> Operation:
    """
    Create one operation and attach its decisions and approval plan.

    The shuttle snapshot is created first. The manager verifies that
    snapshot again before attaching each downstream stage.

    Physical shuttle candidates collapsed by verified logical
    deduplication are recorded in the snapshot ledger as SUPERSEDED
    after the decision queue has established the surviving winners.
    """
    operation = manager.begin(
        Path(shuttle_path),
        operation_id=operation_id,
    )

    decisions = build_decision_queue_from_paths(
        shuttle_path=operation.snapshot.shuttle_path,
        movie_libraries=[
            Path(path)
            for path in movie_libraries
        ],
        tv_libraries=[
            Path(path)
            for path in tv_libraries
        ],
    )

    manager.attach_decisions(
        decisions
    )

    account_superseded_snapshot_files(
        manager
    )

    approval_plan = build_approval_plan(
        decisions
    )

    manager.attach_approval_plan(
        approval_plan
    )

    return manager.require_operation()
