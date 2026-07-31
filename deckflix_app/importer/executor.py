from pathlib import Path

from .checksum import verify
from .copier import copy_job
from .mover import atomic_move
from .queue import ImportQueue


def execute(queue: ImportQueue, temp_dir: Path):
    failures = []

    for job in queue.pending():
        try:
            temp_file = copy_job(job, temp_dir)

            if not verify(job.source, temp_file):
                raise RuntimeError("Checksum verification failed")

            job.verified = True

            atomic_move(temp_file, job.destination)

            job.completed = True

        except Exception as exc:
            failures.append((job, exc))

    return failures
