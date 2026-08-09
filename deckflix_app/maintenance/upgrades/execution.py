from pathlib import Path
import shutil

from deckflix_app.config import load_config

from deckflix_app.safety.guard import (
    require_write_access,
)

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

    config = load_config()

    require_write_access(
        config
    )


    journal = UpgradeJournal.load(
        journal_path
    )


    try:

        source = upgrade.source_path

        destination = (
            upgrade.destination_path
        )


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


        journal.update(
            upgrade
        )

        journal.save()


        backup = destination.with_suffix(
            destination.suffix
            + ".deckflix-backup"
        )


        shutil.copy2(
            destination,
            backup,
        )


        temporary = destination.with_suffix(
            destination.suffix
            + ".deckflix-new"
        )


        shutil.copy2(
            source,
            temporary,
        )


        upgrade.status = (
            UpgradeStatus.VERIFYING
        )


        journal.update(
            upgrade
        )

        journal.save()


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


        journal.update(
            upgrade
        )

        journal.save()


        return upgrade


    except Exception:

        upgrade.status = (
            UpgradeStatus.FAILED
        )


        journal.update(
            upgrade
        )

        journal.save()


        raise
