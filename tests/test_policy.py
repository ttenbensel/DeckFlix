"""Tests for the DeckFlix policy engine."""

from pathlib import Path

import pytest

from deckflix_app.config import (
    DeckFlixConfig,
    DeckFlixPaths,
    NetworkPolicy,
)
from deckflix_app.policy import (
    Operation,
    PolicyDeniedError,
    PolicyEngine,
)


def make_config(
    *,
    profile: str = "normal",
    read_only: bool = False,
    low_impact: bool = False,
    require_vpn: bool = False,
    allow_metadata: bool = True,
    allow_jellyfin: bool = True,
) -> DeckFlixConfig:
    return DeckFlixConfig(
        shuttle=Path("/data/shuttle"),
        movie_libraries=(Path("/data/library1/movie"),),
        tv_libraries=(Path("/data/library2/tv"),),
        report_directory=Path("/data/library1/deckflix-logs"),
            import_staging_directory=Path("/data/library1/deckflix-staging"),
review_hold_directory=Path("/data/library1/deckflix-review-hold"),
        paths=DeckFlixPaths(
            quarantine=Path("/data/library1/deckflix-quarantine"),
            repair_log=Path("/data/library1/deckflix-logs/repair.log"),
        ),
        read_only=read_only,
        operating_profile=profile,
        low_impact=low_impact,
        network=NetworkPolicy(
            require_vpn=require_vpn,
            max_download_mbps=5,
            max_concurrent_downloads=1,
            allow_metadata_downloads=allow_metadata,
            allow_jellyfin_refresh=allow_jellyfin,
        ),
        source_path=Path("config/local.json"),
    )


def test_normal_profile_allows_network() -> None:
    policy = PolicyEngine(make_config(profile="normal"))

    decision = policy.decide(Operation.DOWNLOAD_MEDIA)

    assert decision.allowed is True
    assert decision.limited is False


def test_ship_limited_requires_configured_vpn() -> None:
    policy = PolicyEngine(
        make_config(
            profile="ship_limited",
            require_vpn=True,
        )
    )

    decision = policy.decide(Operation.DOWNLOAD_MEDIA)

    assert decision.allowed is True
    assert decision.limited is True
    assert decision.vpn_required is True


def test_ship_offline_blocks_network() -> None:
    policy = PolicyEngine(make_config(profile="ship_offline"))

    decision = policy.decide(Operation.USE_NETWORK)

    assert decision.allowed is False
    assert "Ship Offline" in decision.reason


def test_ship_offline_still_allows_local_scan() -> None:
    policy = PolicyEngine(make_config(profile="ship_offline"))

    assert policy.can(Operation.SCAN_LOCAL) is True


def test_read_only_blocks_import() -> None:
    policy = PolicyEngine(make_config(read_only=True))

    decision = policy.decide(Operation.IMPORT_MEDIA)

    assert decision.allowed is False
    assert "read-only" in decision.reason


def test_read_only_still_allows_scanning() -> None:
    policy = PolicyEngine(make_config(read_only=True))

    assert policy.can(Operation.SCAN_LOCAL) is True


def test_import_requires_operator_approval() -> None:
    policy = PolicyEngine(make_config())

    decision = policy.decide(Operation.IMPORT_MEDIA)

    assert decision.allowed is True
    assert decision.approval_required is True


def test_delete_requires_operator_approval() -> None:
    policy = PolicyEngine(make_config())

    decision = policy.decide(Operation.DELETE_MEDIA)

    assert decision.allowed is True
    assert decision.approval_required is True


def test_metadata_can_be_disabled_separately() -> None:
    policy = PolicyEngine(
        make_config(
            profile="ship_limited",
            allow_metadata=False,
        )
    )

    assert policy.can_download() is True
    assert policy.can_download_metadata() is False


def test_jellyfin_refresh_can_be_disabled_separately() -> None:
    policy = PolicyEngine(
        make_config(
            profile="ship_limited",
            allow_jellyfin=False,
        )
    )

    assert policy.can_refresh_jellyfin() is False


def test_low_impact_marks_local_operation_as_limited() -> None:
    policy = PolicyEngine(make_config(low_impact=True))

    decision = policy.decide(Operation.SCAN_LOCAL)

    assert decision.allowed is True
    assert decision.limited is True


def test_denied_decision_can_raise() -> None:
    policy = PolicyEngine(make_config(profile="ship_offline"))
    decision = policy.decide(Operation.DOWNLOAD_MEDIA)

    with pytest.raises(PolicyDeniedError):
        decision.require()
