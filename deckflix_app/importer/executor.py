from pathlib import Path

from .engine import ImportEngine
from .queue import ImportQueue


def execute(queue: ImportQueue, temp_dir: Path):
    """
    Backward-compatible wrapper around ImportEngine.

    Existing callers expect a list of ``(job, exception)`` tuples.
    New code should use ImportEngine directly and consume ImportResult.
    """
    result = ImportEngine().execute(queue, temp_dir)

    return [
        (failure.job, failure.error)
        for failure in result.failures
    ]
