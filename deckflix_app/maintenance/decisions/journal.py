import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .models import (
    Decision,
    DecisionType,
)


@dataclass(slots=True)
class DecisionEntry:
    title: str
    decision: str
    classification: str
    reason: str

    source_path: str | None = None
    destination_path: str | None = None

    created_at: str = ""


class DecisionJournal:

    def __init__(
        self,
        path: Path,
    ):

        self.path = path
        self.entries: list[DecisionEntry] = []


    def add(
        self,
        decision: Decision,
    ):

        self.entries.append(
            DecisionEntry(
                title=decision.title,
                decision=decision.decision.value,
                classification=decision.classification,
                reason=decision.reason,
                source_path=(
                    str(decision.source_path)
                    if decision.source_path
                    else None
                ),
                destination_path=(
                    str(decision.destination_path)
                    if decision.destination_path
                    else None
                ),
                created_at=datetime.now().isoformat(),
            )
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
            DecisionEntry(
                **entry
            )
            for entry in data.get(
                "entries",
                [],
            )
        ]

        return journal
