from dataclasses import dataclass


@dataclass(slots=True)
class LibraryPolicy:
    """
    Defines how DeckFlix evaluates imports, upgrades,
    and long-term library management.

    The policy guides recommendations only.
    It never performs automatic deletion.
    """

    profile: str = "Shipboard"

    preferred_resolution: str = "1080p"
    preferred_codec: str = "HEVC"

    maximum_movie_size_gb: float = 10.0
    maximum_episode_size_gb: float = 2.0

    prefer_efficient_upgrades: bool = True

    protect_classics: bool = True
    protect_favourites: bool = True
    protect_complete_series: bool = True

    require_review_above_percent: int = 90

    enable_real_repairs: bool = False

    quarantine_review_days: int = 30
