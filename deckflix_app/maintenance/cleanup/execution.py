from pathlib import Path
import shutil

from .journal import (
    CleanupJournal,
    CleanupStatus,
)

from .plan import (
    CleanupPlan,
    CleanupActionType,
)


def prepare_cleanup(
    plan: CleanupPlan,
    journal_path: Path,
) -> CleanupJournal:

    journal = CleanupJournal.load(
        journal_path,
    )

    if journal.entries:
        return journal


    for action in plan.actions:

        journal.add(
            action=action.action.value,
            path=action.path,
            reason=action.reason,
        )

    journal.save()

    return journal


def execute_cleanup(
    plan: CleanupPlan,
    journal_path: Path,
) -> CleanupJournal:

    journal = prepare_cleanup(
        plan,
        journal_path,
    )


    for index, entry in enumerate(
        journal.entries,
    ):

        if entry.status is CleanupStatus.VERIFIED:
            continue


        if entry.status is CleanupStatus.FAILED:
            break


        try:

            path = entry.path


            if not path.exists():

                journal.update(
                    index,
                    CleanupStatus.VERIFIED,
                )

                journal.save()

                continue


            journal.update(
                index,
                CleanupStatus.REMOVING,
            )

            journal.save()


            if (
                entry.action
                == CleanupActionType.REMOVE_DIRECTORY_TREE.value
            ):

                shutil.rmtree(
                    path
                )


            elif (
                entry.action
                == CleanupActionType.REMOVE_EMPTY_DIRECTORY.value
            ):

                path.rmdir()


            elif (
                entry.action
                == CleanupActionType.REMOVE_FILE.value
            ):

                path.unlink()


            else:

                raise RuntimeError(
                    f"Unknown cleanup action: {entry.action}"
                )


            if path.exists():

                raise RuntimeError(
                    "Cleanup verification failed"
                )


            journal.update(
                index,
                CleanupStatus.VERIFIED,
            )

            journal.save()


        except Exception as exc:

            journal.update(
                index,
                CleanupStatus.FAILED,
                str(exc),
            )

            journal.save()

            break


    return journal
