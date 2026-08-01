from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ImportStage(str, Enum):
    STARTING = "STARTING"
    COPYING = "COPYING"
    VERIFYING = "VERIFYING"
    MOVING = "MOVING"
    COMPLETED = "COMPLETED"
    RESUMED = "RESUMED"
    FAILED = "FAILED"
    FINISHED = "FINISHED"


@dataclass(frozen=True, slots=True)
class ImportProgress:
    stage: ImportStage
    current: int
    total: int
    source: Path | None = None
    destination: Path | None = None
    message: str = ""

    @property
    def percent(self) -> int:
        if self.total <= 0:
            return 0

        return min(
            100,
            int(self.current / self.total * 100),
        )
