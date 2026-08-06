from pathlib import Path
import shutil

from .journal import (
    MaintenanceJournal,
    JournalStatus,
)
from .plan import MaintenancePlan
from .verify import verify_integrity


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


def execute_plan(
    plan: MaintenancePlan,
    journal_path: Path,
) -> MaintenanceJournal:
    """
    Resume-aware maintenance execution.

    COPY
    VERIFY
    REMOVE SOURCE
    """

    journal = prepare_execution(
        plan,
        journal_path,
    )

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

            shutil.copy2(
                source,
                destination,
            )

            result = verify_integrity(
                source,
                destination,
            )

            if not result.success:
                raise RuntimeError(
                    result.reason
                )

            source.unlink()

            journal.update(
                index,
                JournalStatus.VERIFIED,
            )

            journal.save()

        except Exception as exc:
            journal.update(
                index,
                JournalStatus.FAILED,
                str(exc),
            )

            journal.save()

            break

    return journal
