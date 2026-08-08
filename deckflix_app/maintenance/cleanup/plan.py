from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class CleanupActionType(str, Enum):
    REMOVE_EMPTY_DIRECTORY = "REMOVE_EMPTY_DIRECTORY"
    REMOVE_FILE = "REMOVE_FILE"
    REMOVE_DIRECTORY_TREE = "REMOVE_DIRECTORY_TREE"


@dataclass(slots=True)
class CleanupAction:
    action: CleanupActionType
    path: Path
    reason: str


@dataclass(slots=True)
class CleanupPlan:
    source: Path

    actions: list[CleanupAction] = field(
        default_factory=list
    )

    protected_files: int = 0
    review_files: int = 0

    @property
    def total_actions(self) -> int:
        return len(self.actions)
