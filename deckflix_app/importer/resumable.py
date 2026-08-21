from collections.abc import Callable
from pathlib import Path

from .checksum import verify
from .engine import ImportEngine
from .journal import (
    JournalStatus,
    delete_import_journal,
    get_or_create_import_journal,
    job_key,
    mark_journal_completed,
    mark_journal_failed,
    mark_journal_pending,
    save_import_journal,
)
from .progress import ImportProgress, ImportStage
from .queue import ImportQueue
from .results import ImportFailure, ImportResult


ProgressCallback = Callable[[ImportProgress], None]


class ResumableImportExecutor:
    def execute(
        self,
        *,
        operation_id: str,
        queue: ImportQueue,
        temp_dir: Path,
        journal_path: Path,
        progress: ProgressCallback | None = None,
        delete_journal_when_complete: bool = True,
    ) -> ImportResult:
        jobs = list(queue.pending())

        result = ImportResult(total=len(jobs))

        journal = get_or_create_import_journal(
            operation_id=operation_id,
            jobs=jobs,
            journal_path=journal_path,
        )

        self._emit(
            progress,
            ImportProgress(
                stage=ImportStage.STARTING,
                current=journal.completed,
                total=result.total,
                message=(
                    f"Resuming with {journal.completed} "
                    "verified completion(s)"
                ),
            ),
        )

        for job in jobs:
            entry = journal.entries[job_key(job)]

            if self._restore_completed_job(
                job,
                entry.status,
            ):
                try:
                    ImportEngine._retire_replaced_media(
                        job
                    )
                except Exception as error:
                    mark_journal_failed(
                        journal,
                        job,
                        error,
                    )
                    save_import_journal(
                        journal,
                        journal_path,
                    )

                    result.failed += 1
                    result.failures.append(
                        ImportFailure(
                            job=job,
                            error=error,
                        )
                    )

                    self._emit(
                        progress,
                        ImportProgress(
                            stage=ImportStage.FAILED,
                            current=(
                                result.completed
                                + result.failed
                            ),
                            total=result.total,
                            source=job.source,
                            destination=job.destination,
                            message=str(error),
                        ),
                    )
                    continue

                job.completed = True

                mark_journal_completed(journal, job)
                save_import_journal(journal, journal_path)

                result.completed += 1

                self._emit(
                    progress,
                    ImportProgress(
                        stage=ImportStage.RESUMED,
                        current=result.completed + result.failed,
                        total=result.total,
                        source=job.source,
                        destination=job.destination,
                        message=(
                            "Verified existing destination "
                            "and resumed"
                        ),
                    ),
                )
                continue

            if Path(job.destination).exists():
                error = RuntimeError(
                    "Destination exists but does not match the source"
                )

                mark_journal_failed(
                    journal,
                    job,
                    error,
                )
                save_import_journal(journal, journal_path)

                result.failed += 1
                result.failures.append(
                    ImportFailure(
                        job=job,
                        error=error,
                    )
                )

                self._emit(
                    progress,
                    ImportProgress(
                        stage=ImportStage.FAILED,
                        current=result.completed + result.failed,
                        total=result.total,
                        source=job.source,
                        destination=job.destination,
                        message=str(error),
                    ),
                )
                continue

            mark_journal_pending(journal, job)
            save_import_journal(journal, journal_path)

            single_queue = ImportQueue()
            single_queue.add(job)

            completed_before = result.completed + result.failed

            def relay(event: ImportProgress) -> None:
                if event.stage in {
                    ImportStage.STARTING,
                    ImportStage.FINISHED,
                }:
                    return

                self._emit(
                    progress,
                    ImportProgress(
                        stage=event.stage,
                        current=completed_before + event.current,
                        total=result.total,
                        source=event.source,
                        destination=event.destination,
                        message=event.message,
                    ),
                )

            try:
                single_result = ImportEngine().execute(
                    single_queue,
                    Path(temp_dir),
                    progress=relay,
                )

            except BaseException:
                # The destination may already have been atomically moved
                # into the library. The next run reconciles it by checksum
                # and completes any pending upgrade retirement.
                save_import_journal(journal, journal_path)
                raise

            if single_result.completed == 1:
                mark_journal_completed(journal, job)
                result.completed += 1
            else:
                failure = single_result.failures[0]

                mark_journal_failed(
                    journal,
                    job,
                    failure.error,
                )

                result.failed += 1
                result.failures.append(failure)

            save_import_journal(journal, journal_path)

        self._emit(
            progress,
            ImportProgress(
                stage=ImportStage.FINISHED,
                current=result.completed + result.failed,
                total=result.total,
                message=(
                    f"{result.completed} completed, "
                    f"{result.failed} failed"
                ),
            ),
        )

        if (
            delete_journal_when_complete
            and result.failed == 0
            and result.completed == result.total
        ):
            delete_import_journal(journal_path)

        return result

    @staticmethod
    def _restore_completed_job(
        job,
        status: JournalStatus,
    ) -> bool:
        destination = Path(job.destination)

        if not destination.exists():
            return False

        if status not in {
            JournalStatus.COMPLETED,
            JournalStatus.PENDING,
            JournalStatus.FAILED,
        }:
            return False

        try:
            matches = verify(
                Path(job.source),
                destination,
            )
        except OSError:
            return False

        if not matches:
            return False

        job.copied = True
        job.verified = True

        return True

    @staticmethod
    def _emit(
        callback: ProgressCallback | None,
        event: ImportProgress,
    ) -> None:
        if callback is not None:
            callback(event)
