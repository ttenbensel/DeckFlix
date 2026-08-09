from .models import (
    UpgradeCandidate,
    UpgradeType,
    UpgradeStatus,
)

from deckflix_app.maintenance.orphans.duplicates import (
    DuplicateCandidate,
)


def create_upgrade_from_quality(
    item: DuplicateCandidate,
) -> UpgradeCandidate:

    if item.classification.value != "SOURCE_BETTER":

        raise ValueError(
            "Quality item is not an upgrade candidate"
        )


    return UpgradeCandidate(
        title=item.source.title,

        source_path=item.source.path,

        destination_path=(
            item.destination.path
        ),

        upgrade_type=(
            UpgradeType.QUALITY_UPGRADE
        ),

        reason=item.reason,

        status=(
            UpgradeStatus.PENDING
        ),
    )
