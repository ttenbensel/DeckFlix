from dataclasses import dataclass, field

from deckflix_app.models.library_policy import LibraryPolicy


@dataclass(slots=True)
class NetworkPolicy:
    """
    Network behaviour for one operational profile.
    """

    downloads_enabled: bool = True

    use_vpn_for_downloads: bool = True
    require_vpn_for_downloads: bool = True
    vpn_kill_switch: bool = True

    use_vpn_for_metadata: bool = False

    bandwidth_limit_mbps: float | None = None
    download_window: str | None = None


@dataclass(slots=True)
class AutomationPolicy:
    """
    Automatic actions permitted by one operational profile.
    """

    auto_scan_shuttle: bool = True
    auto_import: bool = False
    auto_refresh_jellyfin: bool = True
    auto_quarantine: bool = False


@dataclass(slots=True)
class StoragePolicy:
    """
    Storage limits and review behaviour.
    """

    target_capacity_percent: int = 80
    review_threshold_percent: int = 90

    storage_guardian_enabled: bool = True
    quarantine_review_days: int = 30


@dataclass(slots=True)
class OperationalProfile:
    """
    Complete DeckFlix operating profile.

    Selecting a profile changes policy recommendations and permitted
    behaviour, but never performs an action by itself.
    """

    name: str
    description: str

    library: LibraryPolicy = field(default_factory=LibraryPolicy)
    network: NetworkPolicy = field(default_factory=NetworkPolicy)
    automation: AutomationPolicy = field(default_factory=AutomationPolicy)
    storage: StoragePolicy = field(default_factory=StoragePolicy)
