from collections.abc import Callable
from pathlib import Path

from .checksum import verify
from .copier import copy_job
from .mover import atomic_move
from .progress import ImportProgress, ImportStage
from .queue import ImportQueue
from .results import ImportFailure, ImportResult


ProgressCallback = Callable[[ImportProgress], None]


class ImportEngine:
    def execute(
        self,
        queue: ImportQueue,
        temp_dir: Path,
        *,
        progress: ProgressCallback | None = None,
    ) -> ImportResult:
        result = ImportResult()

        jobs = list(queue.pending())
        result.total = len(jobs)

        temp_dir.mkdir(parents=True, exist_ok=True)

        self._emit(
            progress,
            ImportProgress(
                stage=ImportStage.STARTING,
                current=0,
                total=result.total,
                message="Import operation starting",
            ),
        )

        for index, job in enumerate(jobs, start=1):
            try:
                self._emit(
                    progress,
                    ImportProgress(
                        stage=ImportStage.COPYING,
                        current=index - 1,
                        total=result.total,
                        source=job.source,
                        destination=job.destination,
                        message="Copying to temporary storage",
                    ),
                )

                temp_file = copy_job(job, temp_dir)
                job.copied = True

                self._emit(
                    progress,
                    ImportProgress(
                        stage=ImportStage.VERIFYING,
                        current=index - 1,
                        total=result.total,
                        source=job.source,
                        destination=job.destination,
                        message="Verifying SHA-256 checksum",
                    ),
                )

                if not verify(job.source, temp_file):
                    raise RuntimeError(
                        "Checksum verification failed"
                    )

                job.verified = True

                self._emit(
                    progress,
                    ImportProgress(
                        stage=ImportStage.MOVING,
                        current=index - 1,
                        total=result.total,
                        source=job.source,
                        destination=job.destination,
                        message="Moving verified file into library",
                    ),
                )

                atomic_move(
                    temp_file,
                    job.destination,
                )

                job.completed = True
                result.completed += 1

                self._emit(
                    progress,
                    ImportProgress(
                        stage=ImportStage.COMPLETED,
                        current=index,
                        total=result.total,
                        source=job.source,
                        destination=job.destination,
                        message="File imported and verified",
                    ),
                )

            except Exception as exc:
                result.failed += 1
                result.failures.append(
                    ImportFailure(
                        job=job,
                        error=exc,
                    )
                )

                self._emit(
                    progress,
                    ImportProgress(
                        stage=ImportStage.FAILED,
                        current=index,
                        total=result.total,
                        source=job.source,
                        destination=job.destination,
                        message=str(exc),
                    ),
                )

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

        return result

    @staticmethod
    def _emit(
        callback: ProgressCallback | None,
        event: ImportProgress,
    ) -> None:
        if callback is not None:
            callback(event)
