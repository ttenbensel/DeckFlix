import threading
import time

from .execution import execute_plan
from .progress import MaintenanceProgress
from .progress_display import render_progress


def run_with_progress(
    plan,
    journal_path,
):
    progress = MaintenanceProgress()

    result = {
        "journal": None,
        "error": None,
    }

    started = threading.Event()

    def worker():
        try:
            progress.stage = "PREPARING"
            started.set()

            result["journal"] = execute_plan(
                plan,
                journal_path,
                progress,
            )

        except Exception as exc:
            result["error"] = exc
            started.set()

    thread = threading.Thread(
        target=worker,
        daemon=True,
    )

    thread.start()

    started.wait()

    while thread.is_alive():

        render_progress(
            progress,
        )

        time.sleep(2)

    thread.join()

    if result["error"]:
        progress.stage = "FAILED"
        render_progress(
            progress,
        )
        raise result["error"]

    progress.complete()

    render_progress(
        progress,
    )

    return result["journal"]
