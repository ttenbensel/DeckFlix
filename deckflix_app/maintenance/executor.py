from .plan import MaintenancePlan
from .results import (
    MaintenanceFailure,
    MaintenanceResult,
)


def execute_dry_run(
    plan: MaintenancePlan,
) -> MaintenanceResult:
    """
    Dry-run maintenance executor.

    Reviews planned actions only.
    No files are moved, renamed, or deleted.
    """

    result = MaintenanceResult(
        total=plan.total_actions,
    )

    for action in plan.actions:
        try:
            if not action.source.exists():
                raise FileNotFoundError(
                    action.source
                )

            result.reviewed += 1

        except Exception as exc:
            result.failed += 1

            result.failures.append(
                MaintenanceFailure(
                    action=action,
                    error=exc,
                )
            )

    return result
