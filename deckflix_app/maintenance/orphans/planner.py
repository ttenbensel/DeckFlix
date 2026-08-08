from dataclasses import dataclass, field
from pathlib import Path

from .models import OrphanCandidate, OrphanType


@dataclass
class OrphanCleanupPlan:
    source: Path
    actions: list[OrphanCandidate] = field(
        default_factory=list
    )

    @property
    def total_actions(self):
        return len(self.actions)


def create_orphan_cleanup_plan(
    results: list[OrphanCandidate],
) -> OrphanCleanupPlan:

    source = (
        results[0].path.parent
        if results
        else Path("/")
    )

    plan = OrphanCleanupPlan(
        source=source
    )


    for item in results:

        #
        # Migration leftovers:
        # safe candidates after verification
        #
        if (
            item.classification
            == OrphanType.MIGRATION_LEFTOVER
        ):
            plan.actions.append(
                item
            )


        #
        # Release junk:
        # candidate but requires review
        #
        elif (
            item.classification
            == OrphanType.RELEASE_JUNK
        ):
            plan.actions.append(
                item
            )


        #
        # True orphan movies:
        # DO NOT include
        #
        elif (
            item.classification
            == OrphanType.ORPHAN_MOVIE
        ):
            continue


    return plan
