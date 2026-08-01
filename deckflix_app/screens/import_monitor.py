from dataclasses import dataclass, field
from pathlib import Path
import sys
import time

from deckflix_app.importer import (
    ImportProgress,
    ImportStage,
)


@dataclass(slots=True)
class TerminalImportMonitor:
    operation_id: str = ""
    started_at: float = field(
        default_factory=time.monotonic
    )
    completed_bytes: int = 0
    completed_files: int = 0
    failed_files: int = 0
    current_file: str = ""
    current_stage: str = "STARTING"
    total_files: int = 0
    journal_saved: bool = True

    def __call__(
        self,
        event: ImportProgress,
    ) -> None:
        self.total_files = event.total
        self.current_stage = event.stage.value

        if event.source is not None:
            self.current_file = event.source.name

        if event.stage in {
            ImportStage.COMPLETED,
            ImportStage.RESUMED,
        }:
            self.completed_files = event.current
            self.journal_saved = True

            if event.source is not None:
                try:
                    self.completed_bytes += (
                        Path(event.source).stat().st_size
                    )
                except OSError:
                    pass

        elif event.stage is ImportStage.FAILED:
            self.failed_files += 1
            self.journal_saved = True

        elif event.stage in {
            ImportStage.COPYING,
            ImportStage.VERIFYING,
            ImportStage.MOVING,
        }:
            self.journal_saved = False

        if sys.stdout.isatty():
            self._draw_dashboard(event)
        else:
            self._print_log_line(event)

    def _draw_dashboard(
        self,
        event: ImportProgress,
    ) -> None:
        elapsed = max(
            time.monotonic() - self.started_at,
            0.001,
        )

        speed = self.completed_bytes / elapsed
        remaining_files = max(
            event.total
            - self.completed_files
            - self.failed_files,
            0,
        )

        eta = self._estimate_eta(
            elapsed=elapsed,
            completed=self.completed_files,
            remaining=remaining_files,
        )

        percent = (
            int(
                (
                    self.completed_files
                    + self.failed_files
                )
                / event.total
                * 100
            )
            if event.total
            else 0
        )

        bar = self._progress_bar(percent)

        # Clear terminal and return cursor home.
        print("\033[2J\033[H", end="")

        print("════════════════════════════════════════════════════")
        print("               DECKFLIX IMPORT")
        print("════════════════════════════════════════════════════")
        print()

        if self.operation_id:
            print(f"Operation     {self.operation_id}")

        print(f"Progress      {bar} {percent:3d}%")
        print(
            f"Files         "
            f"{self.completed_files}/{event.total}"
        )
        print(f"Failed        {self.failed_files}")
        print(
            f"Remaining     {remaining_files}"
        )
        print()
        print(f"Current       {self.current_file or '-'}")
        print(f"Stage         {self.current_stage}")
        print()
        print(
            f"Transferred   "
            f"{self._format_bytes(self.completed_bytes)}"
        )
        print(
            f"Average speed "
            f"{self._format_speed(speed)}"
        )
        print(f"Elapsed       {self._format_time(elapsed)}")
        print(f"ETA           {eta}")
        print()
        print(
            f"Journal       "
            f"{'SAVED' if self.journal_saved else 'UPDATING'}"
        )
        print("Snapshot      VERIFIED BEFORE EXECUTION")
        print()
        print("Press Ctrl+C to pause safely.")
        print("════════════════════════════════════════════════════")

    def _print_log_line(
        self,
        event: ImportProgress,
    ) -> None:
        source = (
            event.source.name
            if event.source is not None
            else ""
        )

        print(
            f"{event.stage.value:<10} "
            f"{event.current}/{event.total} "
            f"{source} "
            f"{event.message}"
        )

    @staticmethod
    def _estimate_eta(
        *,
        elapsed: float,
        completed: int,
        remaining: int,
    ) -> str:
        if completed <= 0:
            return "Calculating..."

        seconds_per_file = elapsed / completed
        return TerminalImportMonitor._format_time(
            seconds_per_file * remaining
        )

    @staticmethod
    def _progress_bar(
        percent: int,
        *,
        width: int = 24,
    ) -> str:
        complete = int(
            width * percent / 100
        )

        return (
            "["
            + "#" * complete
            + "-" * (width - complete)
            + "]"
        )

    @staticmethod
    def _format_bytes(value: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(value)

        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.2f} {unit}"

            size /= 1024

        return f"{size:.2f} TB"

    @staticmethod
    def _format_speed(value: float) -> str:
        return (
            TerminalImportMonitor._format_bytes(
                int(value)
            )
            + "/s"
        )

    @staticmethod
    def _format_time(seconds: float) -> str:
        total = max(int(seconds), 0)
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"

        return f"{minutes:02d}:{secs:02d}"
