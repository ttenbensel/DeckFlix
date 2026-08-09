from dataclasses import dataclass


@dataclass(slots=True)
class MissingEpisodeCandidate:
    show: str
    season: int
    episode: int
    reason: str
