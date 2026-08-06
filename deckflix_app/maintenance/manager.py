from pathlib import Path

from .persistence import (
    load_maintenance_plan,
    save_maintenance_plan,
)
from .plan import (
    MaintenancePlan,
    MaintenanceState,
)


class MaintenanceManager:
    """
    Owns maintenance plan lifecycle.

    No files are changed here.
    This only manages plans and approvals.
    """

    def __init__(
        self,
        directory: Path,
    ):
        self.directory = Path(directory)

    def list_plans(self) -> list[Path]:
        if not self.directory.exists():
            return []

        return sorted(
            self.directory.glob(
                "MT-*.json"
            )
        )

    def load(
        self,
        path: Path,
    ) -> MaintenancePlan | None:

        return load_maintenance_plan(
            path
        )

    def approve(
        self,
        plan: MaintenancePlan,
    ) -> MaintenancePlan:

        plan.state = (
            MaintenanceState.APPROVED
        )

        save_maintenance_plan(
            plan,
            self._path_for(plan),
        )

        return plan

    def _path_for(
        self,
        plan: MaintenancePlan,
    ) -> Path:

        return (
            self.directory
            / f"{plan.id}.json"
        )
