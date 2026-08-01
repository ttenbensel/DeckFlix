from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class OperatingMode:
    key: str
    name: str
    icon: str
    motto: str
    description: str

    operating_profile: str
    read_only: bool
    low_impact: bool

    require_vpn: bool
    max_download_mbps: float | None
    max_concurrent_downloads: int
    allow_metadata_downloads: bool
    allow_jellyfin_refresh: bool

    @property
    def display_name(self) -> str:
        return f"{self.icon} {self.name}"

    @property
    def connectivity(self) -> str:
        if not self.allow_metadata_downloads and not self.allow_jellyfin_refresh:
            return "Offline"

        if self.max_download_mbps is not None:
            return f"Limited to {self.max_download_mbps:g} Mbps"

        return "Online"

    @property
    def library_protection(self) -> str:
        return "Enabled" if self.read_only else "Off"


OPERATING_MODES: dict[str, OperatingMode] = {
    "underway": OperatingMode(
        key="underway",
        name="Underway",
        icon="🌊",
        motto="Safe. Self-contained. Reliable.",
        description=(
            "Normal vessel operation with no internet access. "
            "All analysis and import preparation remain local."
        ),
        operating_profile="ship_offline",
        read_only=True,
        low_impact=True,
        require_vpn=False,
        max_download_mbps=None,
        max_concurrent_downloads=1,
        allow_metadata_downloads=False,
        allow_jellyfin_refresh=False,
    ),
    "passage": OperatingMode(
        key="passage",
        name="Passage",
        icon="🛰",
        motto="Connected when it counts.",
        description=(
            "At-sea operation with limited satellite or Starlink access."
        ),
        operating_profile="ship_limited",
        read_only=True,
        low_impact=True,
        require_vpn=True,
        max_download_mbps=5,
        max_concurrent_downloads=1,
        allow_metadata_downloads=True,
        allow_jellyfin_refresh=True,
    ),
    "drydock": OperatingMode(
        key="drydock",
        name="Drydock",
        icon="⚓",
        motto="Repair. Upgrade. Optimise.",
        description=(
            "Full maintenance mode with library writes and network "
            "services available."
        ),
        operating_profile="normal",
        read_only=False,
        low_impact=False,
        require_vpn=False,
        max_download_mbps=None,
        max_concurrent_downloads=4,
        allow_metadata_downloads=True,
        allow_jellyfin_refresh=True,
    ),
    "home_port": OperatingMode(
        key="home_port",
        name="Home Port",
        icon="🏠",
        motto="Your complete media harbour.",
        description=(
            "Full-performance operation for a permanent home installation."
        ),
        operating_profile="normal",
        read_only=False,
        low_impact=False,
        require_vpn=False,
        max_download_mbps=None,
        max_concurrent_downloads=4,
        allow_metadata_downloads=True,
        allow_jellyfin_refresh=True,
    ),
    "workshop": OperatingMode(
        key="workshop",
        name="Workshop",
        icon="🧪",
        motto="Build. Test. Improve.",
        description=(
            "Protected development and testing mode. Production library "
            "writes remain blocked."
        ),
        operating_profile="ship_offline",
        read_only=True,
        low_impact=True,
        require_vpn=False,
        max_download_mbps=None,
        max_concurrent_downloads=1,
        allow_metadata_downloads=False,
        allow_jellyfin_refresh=False,
    ),
}


MODE_ORDER = (
    "underway",
    "passage",
    "drydock",
    "home_port",
    "workshop",
)


def get_operating_mode(key: str) -> OperatingMode:
    try:
        return OPERATING_MODES[key]
    except KeyError as exc:
        raise ValueError(
            f"Unknown DeckFlix operating mode: {key}"
        ) from exc


def infer_operating_mode(config) -> OperatingMode:
    """
    Resolve the friendly operating mode.

    New configurations store ``operating_mode`` directly. Older files are
    mapped from the existing technical profile and safety settings.
    """
    source_path = Path(config.source_path)

    try:
        raw = json.loads(
            source_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        raw = {}

    saved_mode = raw.get("operating_mode")

    if saved_mode in OPERATING_MODES:
        return OPERATING_MODES[saved_mode]

    if config.operating_profile == "ship_offline":
        return OPERATING_MODES["underway"]

    if config.operating_profile == "ship_limited":
        return OPERATING_MODES["passage"]

    if config.read_only:
        return OPERATING_MODES["workshop"]

    return OPERATING_MODES["drydock"]


def mode_changes(
    current_config,
    mode: OperatingMode,
) -> list[str]:
    changes: list[str] = []

    if current_config.read_only != mode.read_only:
        changes.append(
            "Library Protection: "
            + ("Enabled" if mode.read_only else "Off")
        )

    if current_config.low_impact != mode.low_impact:
        changes.append(
            "Low Impact: "
            + ("Enabled" if mode.low_impact else "Off")
        )

    if (
        current_config.operating_profile
        != mode.operating_profile
    ):
        changes.append(
            f"Internal policy: {mode.operating_profile}"
        )

    if (
        current_config.network.allow_metadata_downloads
        != mode.allow_metadata_downloads
    ):
        changes.append(
            "Metadata downloads: "
            + (
                "Allowed"
                if mode.allow_metadata_downloads
                else "Blocked"
            )
        )

    if (
        current_config.network.allow_jellyfin_refresh
        != mode.allow_jellyfin_refresh
    ):
        changes.append(
            "Jellyfin refresh: "
            + (
                "Allowed"
                if mode.allow_jellyfin_refresh
                else "Blocked"
            )
        )

    if (
        current_config.network.max_download_mbps
        != mode.max_download_mbps
    ):
        limit = (
            f"{mode.max_download_mbps:g} Mbps"
            if mode.max_download_mbps is not None
            else "Unlimited"
        )
        changes.append(f"Network limit: {limit}")

    return changes


def apply_operating_mode(
    config_path: Path,
    mode: OperatingMode,
) -> Path:
    """
    Atomically update the existing DeckFlix JSON configuration.

    Media and library paths are preserved unchanged.
    """
    config_path = Path(config_path)

    raw: dict[str, Any] = json.loads(
        config_path.read_text(encoding="utf-8")
    )

    raw["operating_mode"] = mode.key
    raw["operating_profile"] = mode.operating_profile
    raw["read_only"] = mode.read_only
    raw["low_impact"] = mode.low_impact
    raw["network"] = {
        "require_vpn": mode.require_vpn,
        "max_download_mbps": mode.max_download_mbps,
        "max_concurrent_downloads": (
            mode.max_concurrent_downloads
        ),
        "allow_metadata_downloads": (
            mode.allow_metadata_downloads
        ),
        "allow_jellyfin_refresh": (
            mode.allow_jellyfin_refresh
        ),
    }

    temporary = config_path.with_suffix(
        config_path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            raw,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(config_path)

    return config_path
