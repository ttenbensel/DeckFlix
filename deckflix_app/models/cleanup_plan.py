from dataclasses import dataclass, field


@dataclass(slots=True)
class CleanupPlan:
    """
    Read-only repair proposal.

    Nothing in this object performs any filesystem changes.
    It simply describes what DeckFlix recommends.
    """

    release_key: tuple

    keep: list = field(default_factory=list)

    quarantine: list = field(default_factory=list)

    leave: list = field(default_factory=list)

    recovered_bytes: int = 0

    risk: str = "LOW"

    reasons: list[str] = field(default_factory=list)

    @property
    def recovered_gb(self):
        return self.recovered_bytes / 1024**3
