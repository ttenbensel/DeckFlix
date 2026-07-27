from deckflix_app.models.library_policy import LibraryPolicy
from deckflix_app.models.operational_profile import (
    AutomationPolicy,
    NetworkPolicy,
    OperationalProfile,
    StoragePolicy,
)


def shipboard_profile():
    return OperationalProfile(
        name="Shipboard",
        description=(
            "Low-bandwidth, storage-efficient shipboard operation"
        ),
        library=LibraryPolicy(
            profile="Shipboard",
            preferred_resolution="1080p",
            preferred_codec="HEVC",
            maximum_movie_size_gb=10.0,
            maximum_episode_size_gb=2.0,
            require_review_above_percent=90,
        ),
        network=NetworkPolicy(
            downloads_enabled=True,
            use_vpn_for_downloads=True,
            require_vpn_for_downloads=True,
            vpn_kill_switch=True,
            use_vpn_for_metadata=False,
            bandwidth_limit_mbps=2.0,
            download_window="22:00-06:00",
        ),
        automation=AutomationPolicy(
            auto_scan_shuttle=True,
            auto_import=False,
            auto_refresh_jellyfin=True,
            auto_quarantine=False,
        ),
        storage=StoragePolicy(
            target_capacity_percent=80,
            review_threshold_percent=90,
            storage_guardian_enabled=True,
            quarantine_review_days=30,
        ),
    )


def home_profile():
    return OperationalProfile(
        name="Home",
        description="Balanced home use with flexible VPN settings",
        library=LibraryPolicy(
            profile="Home",
            preferred_resolution="1080p",
            preferred_codec="HEVC",
            maximum_movie_size_gb=25.0,
            maximum_episode_size_gb=4.0,
            require_review_above_percent=90,
        ),
        network=NetworkPolicy(
            downloads_enabled=True,
            use_vpn_for_downloads=True,
            require_vpn_for_downloads=False,
            vpn_kill_switch=True,
            use_vpn_for_metadata=False,
            bandwidth_limit_mbps=None,
            download_window=None,
        ),
        automation=AutomationPolicy(
            auto_scan_shuttle=True,
            auto_import=False,
            auto_refresh_jellyfin=True,
            auto_quarantine=False,
        ),
        storage=StoragePolicy(
            target_capacity_percent=85,
            review_threshold_percent=92,
            storage_guardian_enabled=True,
            quarantine_review_days=30,
        ),
    )


def cinema_profile():
    return OperationalProfile(
        name="Cinema",
        description="High-quality home cinema operation",
        library=LibraryPolicy(
            profile="Cinema",
            preferred_resolution="2160p",
            preferred_codec="HEVC",
            maximum_movie_size_gb=80.0,
            maximum_episode_size_gb=12.0,
            require_review_above_percent=92,
        ),
        network=NetworkPolicy(
            downloads_enabled=True,
            use_vpn_for_downloads=True,
            require_vpn_for_downloads=False,
            vpn_kill_switch=True,
            use_vpn_for_metadata=False,
            bandwidth_limit_mbps=None,
            download_window=None,
        ),
        automation=AutomationPolicy(
            auto_scan_shuttle=True,
            auto_import=False,
            auto_refresh_jellyfin=True,
            auto_quarantine=False,
        ),
        storage=StoragePolicy(
            target_capacity_percent=88,
            review_threshold_percent=94,
            storage_guardian_enabled=True,
            quarantine_review_days=30,
        ),
    )


def lab_profile():
    return OperationalProfile(
        name="Lab",
        description="Testing and development profile",
        library=LibraryPolicy(
            profile="Lab",
            preferred_resolution="1080p",
            preferred_codec="HEVC",
            maximum_movie_size_gb=25.0,
            maximum_episode_size_gb=4.0,
            require_review_above_percent=95,
        ),
        network=NetworkPolicy(
            downloads_enabled=True,
            use_vpn_for_downloads=False,
            require_vpn_for_downloads=False,
            vpn_kill_switch=False,
            use_vpn_for_metadata=False,
            bandwidth_limit_mbps=None,
            download_window=None,
        ),
        automation=AutomationPolicy(
            auto_scan_shuttle=True,
            auto_import=False,
            auto_refresh_jellyfin=True,
            auto_quarantine=False,
        ),
        storage=StoragePolicy(
            target_capacity_percent=95,
            review_threshold_percent=98,
            storage_guardian_enabled=True,
            quarantine_review_days=7,
        ),
    )


PROFILE_BUILDERS = {
    "shipboard": shipboard_profile,
    "home": home_profile,
    "cinema": cinema_profile,
    "lab": lab_profile,
}


def get_profile(name):
    builder = PROFILE_BUILDERS.get(name.strip().lower())

    if builder is None:
        raise ValueError(f"Unknown operational profile: {name}")

    return builder()
