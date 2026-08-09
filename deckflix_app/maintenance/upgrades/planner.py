from .models import (
    UpgradeCandidate,
    UpgradeStatus,
    UpgradeType,
)

from pathlib import Path


def create_upgrade_plan(
    title: str,
    source: Path,
    destination: Path,
    reason: str,
) -> UpgradeCandidate:

    return UpgradeCandidate(
        title=title,
        source_path=source,
        destination_path=destination,
        upgrade_type=(
            UpgradeType.QUALITY_UPGRADE
        ),
        reason=reason,
        status=(
            UpgradeStatus.PENDING
        ),
    )
