from dataclasses import dataclass
from pathlib import Path

from .plan import MaintenancePlan


@dataclass(slots=True)
class MaintenancePreflight:
    total_actions: int
    missing_sources: int
    destination_conflicts: int
    estimated_bytes: int

    @property
    def safe(self) -> bool:
        return (
            self.missing_sources == 0
            and self.destination_conflicts == 0
        )


def run_preflight(
    plan: MaintenancePlan,
) -> MaintenancePreflight:
    missing_sources = 0
    destination_conflicts = 0
    estimated_bytes = 0

    for action in plan.actions:
        if not action.source.exists():
            missing_sources += 1
            continue

        try:
            estimated_bytes += (
                action.source.stat().st_size
            )
        except OSError:
            pass

        if action.destination.exists():
            destination_conflicts += 1

    return MaintenancePreflight(
        total_actions=plan.total_actions,
        missing_sources=missing_sources,
        destination_conflicts=destination_conflicts,
        estimated_bytes=estimated_bytes,
    )
