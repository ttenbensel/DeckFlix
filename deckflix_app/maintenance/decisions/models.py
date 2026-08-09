from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DecisionType(str, Enum):
    UPGRADE = "UPGRADE"
    KEEP = "KEEP"
    IGNORE = "IGNORE"


@dataclass(slots=True)
class Decision:
    title: str
    decision: DecisionType

    classification: str
    reason: str

    source_path: Path | None = None
    destination_path: Path | None = None
