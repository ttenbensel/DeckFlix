from datetime import datetime
import json
from pathlib import Path

from .models import MaintenanceAction
from .plan import (
    MaintenancePlan,
    MaintenanceState,
)


PERSISTENCE_VERSION = 1


def _action_to_dict(
    action: MaintenanceAction,
) -> dict:
    return {
        "action": action.action,
        "source": str(action.source),
        "destination": str(action.destination),
        "reason": action.reason,
        "confidence": action.confidence,
    }


def _action_from_dict(
    data: dict,
) -> MaintenanceAction:
    return MaintenanceAction(
        action=data["action"],
        source=Path(data["source"]),
        destination=Path(data["destination"]),
        reason=data["reason"],
        confidence=int(
            data.get(
                "confidence",
                100,
            )
        ),
    )


def plan_to_dict(
    plan: MaintenancePlan,
) -> dict:
    return {
        "version": PERSISTENCE_VERSION,
        "id": plan.id,
        "state": plan.state.value,
        "created_at": (
            plan.created_at.isoformat()
        ),
        "actions": [
            _action_to_dict(action)
            for action in plan.actions
        ],
    }


def plan_from_dict(
    data: dict,
) -> MaintenancePlan:
    if int(
        data.get(
            "version",
            0,
        )
    ) != PERSISTENCE_VERSION:
        raise ValueError(
            "Unsupported maintenance persistence version"
        )

    return MaintenancePlan(
        id=data["id"],
        created_at=datetime.fromisoformat(
            data["created_at"]
        ),
        state=MaintenanceState(
            data["state"]
        ),
        actions=[
            _action_from_dict(action)
            for action in data.get(
                "actions",
                [],
            )
        ],
    )


def save_maintenance_plan(
    plan: MaintenancePlan,
    destination: Path,
) -> Path:
    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            plan_to_dict(plan),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(destination)

    return destination


def load_maintenance_plan(
    source: Path,
) -> MaintenancePlan | None:
    source = Path(source)

    if not source.exists():
        return None

    data = json.loads(
        source.read_text(
            encoding="utf-8"
        )
    )

    return plan_from_dict(data)
