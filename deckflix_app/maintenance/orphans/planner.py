from dataclasses import dataclass, field
from pathlib import Path

from .models import (
    OrphanCandidate,
    OrphanType,
)


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
    include_release_junk: bool = False,
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
        # Safe automatic cleanup
        #
        if (
            item.classification
            == OrphanType.MIGRATION_LEFTOVER
        ):
            plan.actions.append(
                item
            )

            continue


        #
        # Optional cleanup
        #
        if (
            item.classification
            == OrphanType.RELEASE_JUNK
            and include_release_junk
        ):
            plan.actions.append(
                item
            )

            continue


        #
        # Manual review only
        #
        if item.classification in {
            OrphanType.ORPHAN_MOVIE,
            OrphanType.COLLECTION_CONTAINER,
        }:
            continue


    return plan
