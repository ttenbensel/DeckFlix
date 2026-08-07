from dataclasses import dataclass
from datetime import datetime


@dataclass
class MaintenanceProgress:
    stage: str = "PREPARING"

    total_files: int = 0
    completed_files: int = 0

    total_bytes: int = 0
    completed_bytes: int = 0

    current_file: str = ""

    started_at: datetime | None = None
    finished_at: datetime | None = None

    def start(self):
        self.started_at = datetime.now()

    def complete(self):
        self.finished_at = datetime.now()
        self.stage = "COMPLETE"

    @property
    def percent(self) -> float:
        if self.total_files == 0:
            return 0

        return (
            self.completed_files
            / self.total_files
        ) * 100

    @property
    def elapsed_seconds(self) -> float:
        if not self.started_at:
            return 0

        end = (
            self.finished_at
            or datetime.now()
        )

        return (
            end - self.started_at
        ).total_seconds()

    @property
    def bytes_per_second(self) -> float:
        elapsed = self.elapsed_seconds

        if elapsed <= 0:
            return 0

        return (
            self.completed_bytes
            / elapsed
        )

    @property
    def eta_seconds(self) -> float:
        speed = self.bytes_per_second

        if speed <= 0:
            return 0

        remaining = (
            self.total_bytes
            - self.completed_bytes
        )

        return remaining / speed
