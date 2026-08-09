from pathlib import Path
import shutil

from .journal import UpgradeJournal
from .models import (
    UpgradeCandidate,
    UpgradeStatus,
)

from deckflix_app.maintenance.verify import (
    verify_integrity,
)


def execute_upgrade(
    upgrade: UpgradeCandidate,
    journal_path: Path,
) -> UpgradeCandidate:

    journal = UpgradeJournal.load(
        journal_path
    )

    try:

        source = upgrade.source_path
        destination = upgrade.destination_path


        if not source.exists():

            raise FileNotFoundError(
                source
            )


        if not destination.exists():

            raise FileNotFoundError(
                destination
            )


        upgrade.status = (
            UpgradeStatus.BACKUP
        )


        backup = destination.with_suffix(
            destination.suffix
            + ".deckflix-backup"
        )


        shutil.copy2(
            destination,
            backup,
        )


        upgrade.status = (
            UpgradeStatus.VERIFYING
        )


        temporary = destination.with_suffix(
            destination.suffix
            + ".deckflix-new"
        )


        shutil.copy2(
            source,
            temporary,
        )


        result = verify_integrity(
            source,
            temporary,
        )


        if not result.success:

            raise RuntimeError(
                result.reason
            )


        temporary.replace(
            destination
        )


        upgrade.status = (
            UpgradeStatus.EXECUTED
        )


        journal.add(
            upgrade
        )

        journal.save()


        return upgrade


    except Exception:

        upgrade.status = (
            UpgradeStatus.FAILED
        )


        journal.add(
            upgrade
        )

        journal.save()

        raise
