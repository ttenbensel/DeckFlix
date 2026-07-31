from dataclasses import dataclass, field
from pathlib import Path

from .queue import ImportQueue
from .results import ImportResult


@dataclass(slots=True)
class ShuttleSafetyResult:
    safe: bool
    reasons: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "SAFE TO EMPTY" if self.safe else "NOT SAFE TO EMPTY"


class ShuttleSafetyChecker:
    def check(
        self,
        *,
        queue: ImportQueue,
        import_result: ImportResult,
        shuttle_path: Path,
        temp_dir: Path,
    ) -> ShuttleSafetyResult:
        reasons: list[str] = []

        if not shuttle_path.exists():
            reasons.append("Shuttle path is not available")

        if not shuttle_path.is_dir():
            reasons.append("Shuttle path is not a directory")

        if import_result.total == 0:
            reasons.append("No import jobs were processed")

        if import_result.failed:
            reasons.append(
                f"{import_result.failed} import job(s) failed"
            )

        if import_result.completed != import_result.total:
            reasons.append(
                "Not all import jobs completed successfully"
            )

        pending_jobs = list(queue.pending())
        if pending_jobs:
            reasons.append(
                f"{len(pending_jobs)} import job(s) remain pending"
            )

        incomplete_jobs = [
            job
            for job in queue.jobs
            if not job.copied
            or not job.verified
            or not job.completed
        ]
        if incomplete_jobs:
            reasons.append(
                f"{len(incomplete_jobs)} import job(s) lack complete "
                "copy, verification, or completion state"
            )

        missing_destinations = [
            job.destination
            for job in queue.jobs
            if job.completed and not job.destination.exists()
        ]
        if missing_destinations:
            reasons.append(
                f"{len(missing_destinations)} completed destination "
                "file(s) are missing"
            )

        temp_files = []
        if temp_dir.exists():
            temp_files = [
                path
                for path in temp_dir.rglob("*")
                if path.is_file()
            ]

        if temp_files:
            reasons.append(
                f"{len(temp_files)} temporary import file(s) remain"
            )

        return ShuttleSafetyResult(
            safe=not reasons,
            reasons=reasons,
        )
