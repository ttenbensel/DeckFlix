from datetime import datetime
from pathlib import Path

from deckflix_app.decision import ApprovalStatus
from deckflix_app.importer import (
    ImportJob,
    ResumableImportExecutor,
    ImportQueue,
    ShuttleCertificate,
    ShuttleSafetyChecker,
    delete_import_journal,
    sha256,
)

from .history import (
    record_from_manager,
    save_history_record,
)

from .destination import (
    destination_for_media,
)
from .manager import (
    InvalidOperationTransition,
    OperationManager,
)
from .preflight import (
    run_import_preflight,
)


def approve_ready_items(
    manager: OperationManager,
) -> int:
    operation = (
        manager.require_operation()
    )

    manager.require_valid_snapshot()

    if manager.approval_plan is None:
        raise InvalidOperationTransition(
            "No approval plan is attached"
        )

    if (
        operation.state.value
        != "SNAPSHOT_READY"
    ):
        raise InvalidOperationTransition(
            f"Cannot approve items while state is "
            f"{operation.state.value}"
        )

    approved = 0

    for item in manager.approval_plan.items:
        if (
            item.status
            is ApprovalStatus.READY
        ):
            item.status = (
                ApprovalStatus.APPROVED
            )

            approved += 1

    manager.approve()

    return approved


def build_operation_import_queue(
    manager: OperationManager,
    *,
    movie_library: Path,
    tv_library: Path,
    allow_existing_destinations: bool = False,
) -> ImportQueue:
    manager.require_valid_snapshot()

    if manager.approval_plan is None:
        raise InvalidOperationTransition(
            "No approval plan is attached"
        )

    queue = ImportQueue()

    for approval in (
        manager.approval_plan.approved()
    ):
        item = approval.queue_item
        media = item.incoming

        if media.path is None:
            raise ValueError(
                "Approved media has no source "
                f"path: {media.title}"
            )

        destination = destination_for_media(
            media,
            movie_library=movie_library,
            tv_library=tv_library,
        )

        if (
            destination.exists()
            and not allow_existing_destinations
        ):
            raise FileExistsError(
                "Destination already exists: "
                f"{destination}"
            )

        replace_path = None

        if (
            item.decision.action.value
            == "UPGRADE"
        ):
            if (
                item.existing is None
                or item.existing.path is None
            ):
                raise InvalidOperationTransition(
                    "Approved UPGRADE has no "
                    "existing library path: "
                    f"{media.title}"
                )

            replace_path = (
                Path(item.existing.path)
            )

        queue.add(
            ImportJob(
                source=media.path,
                destination=destination,
                decision=item.decision,
                replace_path=replace_path,
            )
        )

    return queue


def record_imported_jobs(
    manager: OperationManager,
    queue: ImportQueue,
) -> int:
    """
    Record successfully imported and verified jobs in
    the snapshot disposition ledger.

    Call only after the import destination audit passes.
    """
    operation = (
        manager.require_operation()
    )

    ledger = (
        manager.require_ledger()
    )

    shuttle_path = (
        operation.snapshot
        .shuttle_path
        .resolve()
    )

    recorded = 0

    for job in queue.jobs:
        if (
            not job.copied
            or not job.verified
            or not job.completed
        ):
            raise InvalidOperationTransition(
                "Cannot record an incomplete "
                "import job in the snapshot ledger"
            )

        source = (
            Path(job.source)
            .resolve()
        )

        destination = (
            Path(job.destination)
            .resolve()
        )

        try:
            relative_path = (
                source.relative_to(
                    shuttle_path
                )
            )

        except ValueError as error:
            raise InvalidOperationTransition(
                "Imported source is outside "
                "the operation shuttle: "
                f"{source}"
            ) from error

        if not destination.exists():
            raise InvalidOperationTransition(
                "Cannot record imported media "
                "because the destination is missing: "
                f"{destination}"
            )

        destination_sha256 = (
            sha256(
                destination
            )
        )

        ledger.mark_imported(
            relative_path,
            destination=destination,
            sha256=destination_sha256,
        )

        recorded += 1

    return recorded


def execute_operation(
    manager: OperationManager,
    *,
    movie_library: Path,
    tv_library: Path,
    temp_dir: Path,
    read_only: bool,
    progress=None,
    history_directory: Path | None = None,
    journal_path: Path | None = None,
) -> ShuttleCertificate | None:
    operation = (
        manager.require_operation()
    )

    if read_only:
        return None

    if (
        operation.state.value
        != "APPROVED"
    ):
        raise InvalidOperationTransition(
            "Operation must be APPROVED "
            "before import; "
            f"current state is "
            f"{operation.state.value}"
        )

    active_journal_path = (
        Path(journal_path)
        if journal_path is not None
        else (
            Path(temp_dir)
            / "import-journal.json"
        )
    )

    preflight = run_import_preflight(
        manager,
        movie_library=movie_library,
        tv_library=tv_library,
        temp_dir=Path(temp_dir),
        journal_path=active_journal_path,
    )

    if not preflight.ready:
        reasons: list[str] = []

        if preflight.missing_sources:
            reasons.append(
                f"{len(preflight.missing_sources)} "
                "approved source file(s) are missing"
            )

        if preflight.changed_sources:
            reasons.append(
                f"{len(preflight.changed_sources)} "
                "approved source file(s) changed"
            )

        if preflight.conflicts:
            reasons.append(
                f"{len(preflight.conflicts)} "
                "destination conflict(s)"
            )

        reasons.extend(
            preflight.errors
        )

        if not reasons:
            reasons.append(
                "import preflight is not ready"
            )

        raise InvalidOperationTransition(
            "Import preflight failed: "
            + "; ".join(reasons)
        )

    queue = (
        build_operation_import_queue(
            manager,
            movie_library=movie_library,
            tv_library=tv_library,
            allow_existing_destinations=True,
        )
    )

    if not queue.jobs:
        raise InvalidOperationTransition(
            "No approved import jobs are available"
        )

    manager.begin_import()

    result = (
        ResumableImportExecutor()
        .execute(
            operation_id=operation.id,
            queue=queue,
            temp_dir=Path(temp_dir),
            journal_path=active_journal_path,
            progress=progress,
            delete_journal_when_complete=False,
        )
    )

    checker = (
        ShuttleSafetyChecker()
    )

    safety = checker.check(
        queue=queue,
        import_result=result,
        shuttle_path=(
            operation.snapshot.shuttle_path
        ),
        temp_dir=Path(temp_dir),
        ignored_temp_paths={
            active_journal_path,
        },
    )

    # Only successful, fully audited imports are
    # allowed to become ledger evidence.
    if safety.safe:
        record_imported_jobs(
            manager,
            queue,
        )

    # Operation-based SAFE TO EMPTY requires complete
    # coverage of the immutable shuttle snapshot.
    checker.apply_snapshot_coverage(
        safety,
        ledger=manager.require_ledger(),
        required=True,
    )

    certificate = (
        ShuttleCertificate(
            shuttle_path=(
                operation.snapshot.shuttle_path
            ),
            import_result=result,
            safety=safety,
            created_at=datetime.now(),
        )
    )

    if safety.safe:
        delete_import_journal(
            active_journal_path
        )

        manager.complete(
            import_result=result,
            certificate=certificate,
        )

        if (
            history_directory
            is not None
        ):
            record = (
                record_from_manager(
                    manager
                )
            )

            save_history_record(
                record,
                Path(
                    history_directory
                ),
            )

    else:
        manager.pause_import()

        manager.import_result = (
            result
        )

        manager.certificate = (
            certificate
        )

    return certificate
