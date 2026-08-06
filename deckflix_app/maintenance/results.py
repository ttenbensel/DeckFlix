from dataclasses import dataclass, field

from .models import MaintenanceAction


@dataclass(slots=True)
class MaintenanceFailure:
    action: MaintenanceAction
    error: Exception

    @property
    def message(self) -> str:
        return str(self.error)


@dataclass(slots=True)
class MaintenanceResult:
    total: int = 0
    reviewed: int = 0
    failed: int = 0
    failures: list[MaintenanceFailure] = field(
        default_factory=list
    )

    @property
    def successful(self) -> bool:
        return (
            self.total > 0
            and self.failed == 0
            and self.reviewed == self.total
        )
