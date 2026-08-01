from datetime import datetime
from pathlib import Path

from deckflix_app.decision import ApprovalStatus
from deckflix_app.importer import (
    ImportEngine,
    ImportJob,
    ImportQueue,
    ShuttleCertificate,
    ShuttleSafetyChecker,
)

from .manager import (
    InvalidOperationTransition,
    OperationManager,
)


def destination_for_media(
    media,
    *,
    movie_library: Path,
    tv_library: Path,
) -> Path:
    if media.path is None:
        raise ValueError(
            f"Media has no source path: {media.title}"
        )

    filename = media.path.name

    if media.media_type == "tv":
        if media.season is None:
            raise ValueError(
                f"TV media has no season: {media.title}"
            )

        return (
            Path(tv_library)
            / media.title
            / f"Season {media.season:02d}"
            / filename
        )

    folder = media.title

    if media.year:
        folder = f"{media.title} ({media.year})"

    return Path(movie_library) / folder / filename


def approve_ready_items(
    manager: OperationManager,
) -> int:
    operation = manager.require_operation()
    manager.require_valid_snapshot()

    if manager.approval_plan is None:
        raise InvalidOperationTransition(
            "No approval plan is attached"
        )

    if operation.state.value != "SNAPSHOT_READY":
        raise InvalidOperationTransition(
            f"Cannot approve items while state is "
            f"{operation.state.value}"
        )

    approved = 0

    for item in manager.approval_plan.items:
        if item.status is ApprovalStatus.READY:
            item.status = ApprovalStatus.APPROVED
            approved += 1

    manager.approve()

    return approved


def build_operation_import_queue(
    manager: OperationManager,
    *,
    movie_library: Path,
    tv_library: Path,
) -> ImportQueue:
    manager.require_valid_snapshot()

    if manager.approval_plan is None:
        raise InvalidOperationTransition(
            "No approval plan is attached"
        )

    queue = ImportQueue()

    for approval in manager.approval_plan.approved():
        item = approval.queue_item
        media = item.incoming

        if media.path is None:
            raise ValueError(
                f"Approved media has no source path: "
                f"{media.title}"
            )

        destination = destination_for_media(
            media,
            movie_library=movie_library,
            tv_library=tv_library,
        )

        if destination.exists():
            raise FileExistsError(
                f"Destination already exists: {destination}"
            )

        queue.add(
            ImportJob(
                source=media.path,
                destination=destination,
                decision=item.decision,
            )
        )

    return queue


def execute_operation(
    manager: OperationManager,
    *,
    movie_library: Path,
    tv_library: Path,
    temp_dir: Path,
    read_only: bool,
) -> ShuttleCertificate | None:
    operation = manager.require_operation()

    if read_only:
        return None

    if operation.state.value != "APPROVED":
        raise InvalidOperationTransition(
            f"Operation must be APPROVED before import; "
            f"current state is {operation.state.value}"
        )

    queue = build_operation_import_queue(
        manager,
        movie_library=movie_library,
        tv_library=tv_library,
    )

    if not queue.jobs:
        raise InvalidOperationTransition(
            "No approved import jobs are available"
        )

    manager.begin_import()

    result = ImportEngine().execute(
        queue,
        Path(temp_dir),
    )

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=result,
        shuttle_path=operation.snapshot.shuttle_path,
        temp_dir=Path(temp_dir),
    )

    certificate = ShuttleCertificate(
        shuttle_path=operation.snapshot.shuttle_path,
        import_result=result,
        safety=safety,
        created_at=datetime.now(),
    )

    manager.complete(
        import_result=result,
        certificate=certificate,
    )

    return certificate
