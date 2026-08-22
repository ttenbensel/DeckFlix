from dataclasses import dataclass, field
from pathlib import Path

from .checksum import verify
from .queue import ImportQueue
from .results import ImportResult


@dataclass(slots=True)
class ShuttleSafetyResult:
    safe: bool
    reasons: list[str] = field(default_factory=list)
    audited_files: int = 0
    total_files: int = 0

    snapshot_coverage_required: bool = False
    snapshot_files: int = 0
    snapshot_accounted: int = 0
    snapshot_unresolved: int = 0
    snapshot_imported: int = 0
    snapshot_identical: int = 0
    snapshot_superseded: int = 0
    snapshot_review_hold: int = 0

    @property
    def status(self) -> str:
        return (
            "SAFE TO EMPTY"
            if self.safe
            else "NOT SAFE TO EMPTY"
        )

    @property
    def audit_complete(self) -> bool:
        return (
            self.total_files > 0
            and self.audited_files == self.total_files
        )

    @property
    def snapshot_coverage_complete(self) -> bool:
        if not self.snapshot_coverage_required:
            return True

        return (
            self.snapshot_files > 0
            and self.snapshot_accounted
            == self.snapshot_files
            and self.snapshot_unresolved == 0
        )

    @property
    def snapshot_coverage_percent(self) -> int:
        if self.snapshot_files <= 0:
            return 0

        return int(
            (
                self.snapshot_accounted
                / self.snapshot_files
            )
            * 100
        )


class ShuttleSafetyChecker:
    def check(
        self,
        *,
        queue: ImportQueue,
        import_result: ImportResult,
        shuttle_path: Path,
        temp_dir: Path,
        ignored_temp_paths: set[Path] | None = None,
    ) -> ShuttleSafetyResult:
        reasons: list[str] = []
        audited_files = 0
        total_files = len(queue.jobs)

        if not shuttle_path.exists():
            reasons.append(
                "Shuttle path is not available"
            )

        if not shuttle_path.is_dir():
            reasons.append(
                "Shuttle path is not a directory"
            )

        if import_result.total == 0:
            reasons.append(
                "No import jobs were processed"
            )

        if import_result.failed:
            reasons.append(
                f"{import_result.failed} import job(s) failed"
            )

        if (
            import_result.completed
            != import_result.total
        ):
            reasons.append(
                "Not all import jobs completed successfully"
            )

        pending_jobs = list(
            queue.pending()
        )

        if pending_jobs:
            reasons.append(
                f"{len(pending_jobs)} import job(s) "
                "remain pending"
            )

        incomplete_jobs = [
            job
            for job in queue.jobs
            if (
                not job.copied
                or not job.verified
                or not job.completed
            )
        ]

        if incomplete_jobs:
            reasons.append(
                f"{len(incomplete_jobs)} import job(s) "
                "lack complete copy, verification, "
                "or completion state"
            )

        missing_destinations = [
            job.destination
            for job in queue.jobs
            if not job.destination.exists()
        ]

        if missing_destinations:
            reasons.append(
                f"{len(missing_destinations)} destination "
                "file(s) are missing"
            )

        audit_failures: list[Path] = []

        for job in queue.jobs:
            source = Path(
                job.source
            )

            destination = Path(
                job.destination
            )

            if (
                not source.exists()
                or not destination.exists()
            ):
                audit_failures.append(
                    destination
                )
                continue

            try:
                matches = verify(
                    source,
                    destination,
                )
            except OSError:
                matches = False

            if matches:
                audited_files += 1
            else:
                audit_failures.append(
                    destination
                )

        if audit_failures:
            reasons.append(
                f"{len(audit_failures)} destination "
                "file(s) failed the final SHA-256 audit"
            )

        if (
            total_files > 0
            and audited_files != total_files
        ):
            reasons.append(
                "Final destination audit is incomplete"
            )

        ignored = {
            Path(path).resolve()
            for path in (
                ignored_temp_paths
                or set()
            )
        }

        temp_files: list[Path] = []

        if temp_dir.exists():
            temp_files = [
                path
                for path in temp_dir.rglob("*")
                if (
                    path.is_file()
                    and path.resolve()
                    not in ignored
                )
            ]

        if temp_files:
            reasons.append(
                f"{len(temp_files)} temporary import "
                "file(s) remain"
            )

        return ShuttleSafetyResult(
            safe=not reasons,
            reasons=reasons,
            audited_files=audited_files,
            total_files=total_files,
        )

    def apply_snapshot_coverage(
        self,
        result: ShuttleSafetyResult,
        *,
        ledger,
        required: bool = True,
    ) -> ShuttleSafetyResult:
        """
        Extend an existing import safety result with
        whole-snapshot disposition coverage.

        This deliberately does not repeat the destination
        SHA-256 audit performed by check().
        """
        result.snapshot_coverage_required = required

        if not required:
            result.safe = not result.reasons
            return result

        if ledger is None:
            result.reasons.append(
                "Snapshot disposition ledger is unavailable"
            )

            result.safe = False
            return result

        result.snapshot_files = (
            ledger.total_files
        )

        result.snapshot_accounted = (
            ledger.accounted_files
        )

        result.snapshot_unresolved = (
            ledger.unresolved_files
        )

        result.snapshot_imported = (
            self._ledger_count(
                ledger,
                "IMPORTED",
            )
        )

        result.snapshot_identical = (
            self._ledger_count(
                ledger,
                "IDENTICAL",
            )
        )

        result.snapshot_superseded = (
            self._ledger_count(
                ledger,
                "SUPERSEDED",
            )
        )

        result.snapshot_review_hold = (
            self._ledger_count(
                ledger,
                "REVIEW_HOLD",
            )
        )

        if result.snapshot_files <= 0:
            result.reasons.append(
                "Shuttle snapshot contains no media files"
            )

        if result.snapshot_unresolved:
            result.reasons.append(
                f"{result.snapshot_unresolved} shuttle "
                "snapshot file(s) remain unresolved"
            )

        if (
            result.snapshot_files > 0
            and result.snapshot_accounted
            != result.snapshot_files
        ):
            result.reasons.append(
                "Snapshot disposition coverage is incomplete"
            )

        result.safe = not result.reasons

        return result

    @staticmethod
    def _ledger_count(
        ledger,
        disposition_value: str,
    ) -> int:
        return sum(
            1
            for entry in ledger.entries.values()
            if (
                getattr(
                    entry.disposition,
                    "value",
                    str(entry.disposition),
                )
                == disposition_value
            )
        )
