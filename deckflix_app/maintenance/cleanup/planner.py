from pathlib import Path

from .plan import (
    CleanupPlan,
    CleanupAction,
    CleanupActionType,
)


PROTECTED_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".mov",
    ".srt",
    ".sub",
    ".idx",
    ".nfo",
    ".xml",
}


def create_cleanup_plan(
    source: Path,
) -> CleanupPlan:

    plan = CleanupPlan(
        source=source,
    )


    for item in source.rglob("*"):

        if item.is_dir():

            try:
                next(item.iterdir())

            except StopIteration:

                plan.actions.append(
                    CleanupAction(
                        action=(
                            CleanupActionType
                            .REMOVE_EMPTY_DIRECTORY
                        ),
                        path=item,
                        reason=(
                            "Empty directory"
                        ),
                    )
                )

            continue


        suffix = item.suffix.lower()


        if suffix in PROTECTED_EXTENSIONS:

            plan.protected_files += 1

            continue


        name = item.name.lower()


        if (
            name.endswith(".txt")
            and (
                "torrent" in name
                or "tgx" in name
                or "yts" in name
                or "proxy" in name
            )
        ):

            plan.actions.append(
                CleanupAction(
                    action=(
                        CleanupActionType
                        .REMOVE_FILE
                    ),
                    path=item,
                    reason=(
                        "Torrent attribution file"
                    ),
                )
            )

        else:

            plan.review_files += 1


    return plan
