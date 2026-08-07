from pathlib import Path
import shutil

from .journal import (
    MaintenanceJournal,
    JournalStatus,
)
from .plan import MaintenancePlan
from .verify import verify_integrity
from .snapshot import MaintenanceSnapshot
from .progress import MaintenanceProgress


def prepare_execution(
    plan: MaintenancePlan,
    journal_path: Path,
) -> MaintenanceJournal:
    """
    Prepare a maintenance execution journal.

    No files are changed.
    """

    journal = MaintenanceJournal.load(
        journal_path,
    )

    if journal.entries:
        return journal

    for action in plan.actions:
        journal.add(
            action.source,
            action.destination,
        )

    journal.save()

    return journal


def create_plan_snapshot(
    plan: MaintenancePlan,
) -> MaintenanceSnapshot:
    """
    Capture the approved source files
    before execution.
    """

    sources = [
        action.source
        for action in plan.actions
    ]

    return MaintenanceSnapshot.create(
        sources,
    )


def execute_plan(
    plan: MaintenancePlan,
    journal_path: Path,
    progress: MaintenanceProgress | None = None,
) -> MaintenanceJournal:
    """
    Resume-aware maintenance execution.

    Safety flow:

    JOURNAL
    SNAPSHOT
    VERIFY
    COPY
    VERIFY DESTINATION
    JOURNAL COMPLETE
    REMOVE SOURCE
    """

    journal = prepare_execution(
        plan,
        journal_path,
    )

    if progress:
        progress.stage = "SNAPSHOT"
        progress.total_files = len(
            journal.entries
        )
        progress.total_bytes = sum(
            entry.source_size or 0
            for entry in journal.entries
        )
        progress.start()

    snapshot = create_plan_snapshot(
        plan,
    )

    if not snapshot.verify():
        raise RuntimeError(
            "Source snapshot verification failed"
        )

    if progress:
        progress.stage = "COPYING"

    for index, entry in enumerate(
        journal.entries,
    ):

        if entry.status is JournalStatus.VERIFIED:
            continue

        if entry.status is JournalStatus.FAILED:
            break

        try:
            source = entry.source
            destination = entry.destination

            if progress:
                progress.current_file = (
                    source.name
                )

            if not source.exists():
                raise FileNotFoundError(
                    source
                )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            journal.update(
                index,
                JournalStatus.MOVING,
            )

            journal.save()

            if progress:
                progress.stage = "COPYING"

            shutil.copy2(
                source,
                destination,
            )

            if progress:
                progress.stage = "VERIFYING"

            result = verify_integrity(
                source,
                destination,
            )

            if not result.success:
                raise RuntimeError(
                    result.reason
                )

            journal.update(
                index,
                JournalStatus.VERIFIED,
            )

            journal.save()

            if progress:
                progress.completed_files += 1
                progress.completed_bytes += (
                    entry.source_size or 0
                )

            if progress:
                progress.stage = "REMOVING SOURCE"

            source.unlink()

        except Exception as exc:
            journal.update(
                index,
                JournalStatus.FAILED,
                str(exc),
            )

            journal.save()

            break

    if progress:
        progress.stage = "COMPLETE"

    return journal
