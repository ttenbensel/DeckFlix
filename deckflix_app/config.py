"""DeckFlix configuration loading and validation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/local.json")
CONFIG_ENVIRONMENT_VARIABLE = "DECKFLIX_CONFIG"

VALID_OPERATING_PROFILES = {
    "normal",
    "ship_limited",
    "ship_offline",
}


class ConfigurationError(RuntimeError):
    """Raised when DeckFlix configuration is missing or invalid."""


@dataclass(frozen=True)
class NetworkPolicy:
    """Network restrictions applied by the active operating profile."""

    require_vpn: bool = False
    max_download_mbps: float | None = None
    max_concurrent_downloads: int = 1
    allow_metadata_downloads: bool = True
    allow_jellyfin_refresh: bool = True


@dataclass(frozen=True)
class DeckFlixPaths:
    """Runtime paths used by DeckFlix services."""

    quarantine: Path
    repair_log: Path


@dataclass(frozen=True)
class DeckFlixConfig:
    """Validated DeckFlix runtime configuration."""

    shuttle: Path
    movie_libraries: tuple[Path, ...]
    tv_libraries: tuple[Path, ...]
    report_directory: Path
    import_staging_directory: Path
    review_hold_directory: Path
    paths: DeckFlixPaths
    read_only: bool
    operating_profile: str
    low_impact: bool
    network: NetworkPolicy
    source_path: Path

    @property
    def network_allowed(self) -> bool:
        """Return whether outbound network operations are permitted."""

        return self.operating_profile != "ship_offline"

    @property
    def downloads_allowed(self) -> bool:
        """Return whether download integrations may operate."""

        return self.operating_profile in {"normal", "ship_limited"}


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(
            f"Configuration value '{key}' must be a non-empty string."
        )

    return value.strip()


def _read_path_list(data: dict[str, Any], key: str) -> tuple[Path, ...]:
    value = data.get(key)

    if not isinstance(value, list) or not value:
        raise ConfigurationError(
            f"Configuration value '{key}' must contain at least one path."
        )

    paths: list[Path] = []

    for position, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ConfigurationError(
                f"Configuration value '{key}[{position}]' "
                "must be a non-empty string."
            )

        paths.append(Path(item).expanduser())

    return tuple(paths)


def _read_network_policy(data: dict[str, Any]) -> NetworkPolicy:
    network_data = data.get("network", {})

    if not isinstance(network_data, dict):
        raise ConfigurationError(
            "Configuration value 'network' must be an object."
        )

    max_download_mbps = network_data.get("max_download_mbps")

    if max_download_mbps is not None:
        if (
            not isinstance(max_download_mbps, (int, float))
            or isinstance(max_download_mbps, bool)
            or max_download_mbps <= 0
        ):
            raise ConfigurationError(
                "'network.max_download_mbps' must be greater than zero "
                "or null."
            )

        max_download_mbps = float(max_download_mbps)

    max_concurrent = network_data.get("max_concurrent_downloads", 1)

    if (
        not isinstance(max_concurrent, int)
        or isinstance(max_concurrent, bool)
        or max_concurrent < 1
    ):
        raise ConfigurationError(
            "'network.max_concurrent_downloads' must be an integer "
            "of at least 1."
        )

    return NetworkPolicy(
        require_vpn=bool(network_data.get("require_vpn", False)),
        max_download_mbps=max_download_mbps,
        max_concurrent_downloads=max_concurrent,
        allow_metadata_downloads=bool(
            network_data.get("allow_metadata_downloads", True)
        ),
        allow_jellyfin_refresh=bool(
            network_data.get("allow_jellyfin_refresh", True)
        ),
    )


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    """Resolve the configuration path from an argument, environment, or default."""

    if config_path is not None:
        return Path(config_path).expanduser()

    environment_path = os.environ.get(CONFIG_ENVIRONMENT_VARIABLE)

    if environment_path:
        return Path(environment_path).expanduser()

    return DEFAULT_CONFIG_PATH


def load_config(
    config_path: str | Path | None = None,
    *,
    validate_paths: bool = True,
) -> DeckFlixConfig:
    """Load and validate DeckFlix configuration."""

    path = resolve_config_path(config_path)

    if not path.is_file():
        raise ConfigurationError(
            f"DeckFlix configuration file not found: {path}\n"
            "Create config/local.json from config/example.json or set "
            f"{CONFIG_ENVIRONMENT_VARIABLE}."
        )

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigurationError(
            f"Invalid JSON in {path}: line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    except OSError as error:
        raise ConfigurationError(
            f"Unable to read DeckFlix configuration {path}: {error}"
        ) from error

    if not isinstance(raw_data, dict):
        raise ConfigurationError(
            "The DeckFlix configuration root must be a JSON object."
        )

    operating_profile = raw_data.get("operating_profile", "normal")

    if operating_profile not in VALID_OPERATING_PROFILES:
        choices = ", ".join(sorted(VALID_OPERATING_PROFILES))
        raise ConfigurationError(
            f"Unknown operating profile '{operating_profile}'. "
            f"Expected one of: {choices}."
        )

    config = DeckFlixConfig(
        shuttle=Path(_require_string(raw_data, "shuttle")).expanduser(),
        movie_libraries=_read_path_list(raw_data, "movie_libraries"),
        tv_libraries=_read_path_list(raw_data, "tv_libraries"),
        report_directory=Path(
            _require_string(raw_data, "report_directory")
        ).expanduser(),
        import_staging_directory=Path(
            _require_string(raw_data, "import_staging_directory")
        ).expanduser(),
        review_hold_directory=Path(
            _require_string(raw_data, "review_hold_directory")
        ).expanduser(),
        paths=DeckFlixPaths(
            quarantine=Path(
                _require_string(raw_data, "quarantine_directory")
            ).expanduser(),
            repair_log=Path(
                _require_string(raw_data, "repair_log")
            ).expanduser(),
        ),
        read_only=bool(raw_data.get("read_only", True)),
        operating_profile=operating_profile,
        low_impact=bool(raw_data.get("low_impact", False)),
        network=_read_network_policy(raw_data),
        source_path=path,
    )

    if validate_paths:
        validate_config_paths(config)

    return config


def validate_config_paths(config: DeckFlixConfig) -> None:
    """Validate configured storage paths without changing the filesystem."""

    missing_paths: list[str] = []

    required_directories = (
        ("shuttle", config.shuttle),
        *(
            (f"movie_libraries[{index}]", library)
            for index, library in enumerate(config.movie_libraries)
        ),
        *(
            (f"tv_libraries[{index}]", library)
            for index, library in enumerate(config.tv_libraries)
        ),
    )

    for name, path in required_directories:
        if not path.exists():
            missing_paths.append(f"{name}: {path}")
        elif not path.is_dir():
            raise ConfigurationError(
                f"Configured path '{name}' is not a directory: {path}"
            )

    if missing_paths:
        formatted = "\n".join(f"  - {item}" for item in missing_paths)
        raise ConfigurationError(
            "The following configured paths do not exist:\n"
            f"{formatted}"
        )

    writable_path_parents = (
        ("report_directory", config.report_directory.parent),
        (
            "import_staging_directory",
            config.import_staging_directory.parent,
        ),
        (
            "review_hold_directory",
            config.review_hold_directory.parent,
        ),
        ("quarantine_directory", config.paths.quarantine.parent),
        ("repair_log", config.paths.repair_log.parent),
    )

    for name, parent in writable_path_parents:
        if not parent.exists():
            raise ConfigurationError(
                f"The parent of configured path '{name}' does not exist: "
                f"{parent}"
            )

        if not parent.is_dir():
            raise ConfigurationError(
                f"The parent of configured path '{name}' is not a directory: "
                f"{parent}"
            )
