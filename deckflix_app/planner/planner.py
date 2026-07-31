from collections import Counter
from dataclasses import dataclass

from deckflix_app.decision import Action, Decision


@dataclass(slots=True)
class ImportPlan:
    total: int
    new: int
    upgrades: int
    duplicates: int
    downgrades: int
    total_bytes: int


def build_import_plan(
    decisions: list[Decision],
    total_bytes: int = 0,
) -> ImportPlan:

    counts = Counter(d.action for d in decisions)

    return ImportPlan(
        total=len(decisions),
        new=counts[Action.NEW],
        upgrades=counts[Action.UPGRADE],
        duplicates=counts[Action.DUPLICATE],
        downgrades=counts[Action.DOWNGRADE],
        total_bytes=total_bytes,
    )
