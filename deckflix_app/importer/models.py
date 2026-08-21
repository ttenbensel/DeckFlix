from dataclasses import dataclass
from pathlib import Path

from deckflix_app.decision import Decision


@dataclass(slots=True)
class ImportJob:
    source: Path
    destination: Path
    decision: Decision
    replace_path: Path | None = None
    verified: bool = False
    copied: bool = False
    completed: bool = False
