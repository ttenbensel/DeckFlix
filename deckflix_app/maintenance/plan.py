from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4

from .models import MaintenanceAction


class MaintenanceState(str, Enum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETE = "COMPLETE"


@dataclass(slots=True)
class MaintenancePlan:
    actions: list[MaintenanceAction]
    created_at: datetime
    id: str
    state: MaintenanceState = MaintenanceState.CREATED

    @property
    def total_actions(self) -> int:
        return len(self.actions)


def create_plan(
    actions: list[MaintenanceAction],
) -> MaintenancePlan:
    return MaintenancePlan(
        actions=actions,
        created_at=datetime.now(),
        id=f"MT-{uuid4().hex[:8].upper()}",
    )
