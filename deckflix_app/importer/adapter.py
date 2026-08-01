from collections.abc import Iterable
from pathlib import Path
from typing import Any

from deckflix_app.decision import Action, Decision

from .models import ImportJob
from .queue import ImportQueue


def decision_for_plan_item(plan_item: dict[str, Any]) -> Decision:
    """
    Convert a legacy approved import-plan item into a typed decision.

    The legacy path only sends approved IMPORT actions here, so these
    jobs represent new media entering the library.
    """
    media = plan_item["media"]

    return Decision(
        action=Action.NEW,
        reason="Approved legacy import",
        existing_score=0,
        incoming_score=getattr(media, "quality_score", 0),
    )


def import_job_from_plan_item(
    plan_item: dict[str, Any],
) -> ImportJob:
    """
    Convert one READY legacy plan item into an ImportJob.

    Existing destinations are rejected so the modern engine is never
    used to overwrite library files accidentally.
    """
    status = plan_item.get("status")

    if status != "READY":
        raise ValueError(
            f"Import plan item is not ready: {status!r}"
        )

    source = Path(plan_item["source"])
    destination = Path(plan_item["target"])

    if destination.exists():
        raise FileExistsError(
            f"Destination already exists: {destination}"
        )

    return ImportJob(
        source=source,
        destination=destination,
        decision=decision_for_plan_item(plan_item),
    )


def queue_from_legacy_plan(
    plan: Iterable[dict[str, Any]],
) -> ImportQueue:
    """
    Build a typed ImportQueue from READY legacy plan items.

    SKIP_EXISTS items are intentionally ignored. Any unexpected status
    is rejected rather than silently imported.
    """
    queue = ImportQueue()

    for item in plan:
        status = item.get("status")

        if status == "SKIP_EXISTS":
            continue

        queue.add(import_job_from_plan_item(item))

    return queue
