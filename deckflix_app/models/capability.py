from dataclasses import dataclass, field


@dataclass(slots=True)
class Capability:
    """
    A user-facing DeckFlix capability.

    A capability represents one workflow rather than one function.
    """

    id: str
    name: str
    description: str

    engines: list[str] = field(default_factory=list)

    destructive: bool = False

    enabled: bool = True

    estimated_steps: int = 0

