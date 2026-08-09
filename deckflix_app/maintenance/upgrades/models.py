from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class UpgradeType(str, Enum):
    QUALITY_UPGRADE = "QUALITY_UPGRADE"


class UpgradeStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


@dataclass(slots=True)
class UpgradeCandidate:
    title: str

    source_path: Path
    destination_path: Path

    upgrade_type: UpgradeType

    reason: str

    status: UpgradeStatus = (
        UpgradeStatus.PENDING
    )

