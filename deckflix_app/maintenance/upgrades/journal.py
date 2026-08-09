import json

from dataclasses import (
    asdict,
    dataclass,
)

from datetime import datetime

from pathlib import Path

from .models import UpgradeCandidate


@dataclass(slots=True)
class UpgradeEntry:
    title: str
    source_path: str
    destination_path: str
    upgrade_type: str
    reason: str
    status: str
    created_at: str
    updated_at: str | None = None


class UpgradeJournal:

    def __init__(
        self,
        path: Path,
    ):

        self.path = path

        self.entries: list[
            UpgradeEntry
        ] = []


    def add(
        self,
        upgrade: UpgradeCandidate,
    ):

        self.entries.append(
            UpgradeEntry(
                title=upgrade.title,
                source_path=str(
                    upgrade.source_path
                ),
                destination_path=str(
                    upgrade.destination_path
                ),
                upgrade_type=(
                    upgrade.upgrade_type.value
                ),
                reason=upgrade.reason,
                status=upgrade.status.value,
                created_at=(
                    datetime.now()
                    .isoformat()
                ),
                updated_at=None,
            )
        )


    def find(
        self,
        upgrade: UpgradeCandidate,
    ):

        for entry in self.entries:

            if (
                entry.source_path
                == str(upgrade.source_path)
                and
                entry.destination_path
                == str(upgrade.destination_path)
            ):

                return entry

        return None


    def update(
        self,
        upgrade: UpgradeCandidate,
    ):

        entry = self.find(
            upgrade
        )

        if not entry:

            self.add(
                upgrade
            )

            return


        entry.status = (
            upgrade.status.value
        )

        entry.updated_at = (
            datetime.now()
            .isoformat()
        )


    def save(self):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path.write_text(
            json.dumps(
                {
                    "entries": [
                        asdict(entry)
                        for entry in self.entries
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )


    @classmethod
    def load(
        cls,
        path: Path,
    ):

        journal = cls(
            path
        )

        if not path.exists():

            return journal


        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )


        journal.entries = [

            UpgradeEntry(
                **entry
            )

            for entry in data.get(
                "entries",
                [],
            )
        ]


        return journal
