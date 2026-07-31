from pathlib import Path

from .checksum import verify
from .copier import copy_job
from .mover import atomic_move
from .queue import ImportQueue
from .results import ImportFailure, ImportResult


class ImportEngine:
    def execute(self, queue: ImportQueue, temp_dir: Path) -> ImportResult:
        result = ImportResult()

        jobs = list(queue.pending())
        result.total = len(jobs)

        temp_dir.mkdir(parents=True, exist_ok=True)

        for job in jobs:
            try:
                temp_file = copy_job(job, temp_dir)
                job.copied = True

                if not verify(job.source, temp_file):
                    raise RuntimeError("Checksum verification failed")

                job.verified = True

                atomic_move(temp_file, job.destination)
                job.completed = True

                result.completed += 1

            except Exception as exc:
                result.failed += 1
                result.failures.append(
                    ImportFailure(
                        job=job,
                        error=exc,
                    )
                )

        return result
