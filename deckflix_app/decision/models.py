from dataclasses import dataclass

from .actions import Action


@dataclass(slots=True)
class Decision:
    action: Action
    reason: str
    existing_score: int
    incoming_score: int
    confidence: int = 100
