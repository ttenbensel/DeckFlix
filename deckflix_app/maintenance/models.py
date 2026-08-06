from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class MaintenanceAction:
    action: str
    source: Path
    destination: Path
    reason: str
    confidence: int = 100
