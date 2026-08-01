import json
from pathlib import Path
from types import SimpleNamespace

from deckflix_app.operating_modes import (
    OPERATING_MODES,
    apply_operating_mode,
    get_operating_mode,
    infer_operating_mode,
)


def make_config_file(tmp_path: Path) -> Path:
    path = tmp_path / "local.json"

    path.write_text(
        json.dumps(
            {
                "shuttle": "/data/shuttle",
                "movie_libraries": ["/data/movies"],
                "tv_libraries": ["/data/tv"],
                "report_directory": "/data/logs",
                "quarantine_directory": "/data/quarantine",
                "repair_log": "/data/logs/repair.log",
                "read_only": True,
                "operating_profile": "ship_limited",
                "low_impact": True,
                "network": {
                    "require_vpn": True,
                    "max_download_mbps": 5,
                    "max_concurrent_downloads": 1,
                    "allow_metadata_downloads": False,
                    "allow_jellyfin_refresh": True,
                },
            }
        ),
        encoding="utf-8",
    )

    return path


def make_config(
    source_path: Path,
    *,
    profile: str = "ship_limited",
    read_only: bool = True,
):
    return SimpleNamespace(
        source_path=source_path,
        operating_profile=profile,
        read_only=read_only,
        low_impact=True,
        network=SimpleNamespace(
            allow_metadata_downloads=False,
            allow_jellyfin_refresh=True,
            max_download_mbps=5,
        ),
    )


def test_all_official_modes_exist():
    assert set(OPERATING_MODES) == {
        "underway",
        "passage",
        "drydock",
        "home_port",
        "workshop",
    }


def test_underway_is_offline_and_protected():
    mode = get_operating_mode("underway")

    assert mode.read_only is True
    assert mode.low_impact is True
    assert mode.allow_metadata_downloads is False
    assert mode.allow_jellyfin_refresh is False
    assert mode.connectivity == "Offline"


def test_passage_is_limited_and_protected():
    mode = get_operating_mode("passage")

    assert mode.read_only is True
    assert mode.max_download_mbps == 5
    assert "5 Mbps" in mode.connectivity


def test_drydock_allows_library_writes():
    mode = get_operating_mode("drydock")

    assert mode.read_only is False
    assert mode.low_impact is False
    assert mode.allow_jellyfin_refresh is True


def test_apply_mode_preserves_storage_paths(
    tmp_path: Path,
):
    path = make_config_file(tmp_path)

    apply_operating_mode(
        path,
        get_operating_mode("underway"),
    )

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    assert data["operating_mode"] == "underway"
    assert data["operating_profile"] == "ship_offline"
    assert data["read_only"] is True
    assert data["low_impact"] is True

    assert data["shuttle"] == "/data/shuttle"
    assert data["movie_libraries"] == ["/data/movies"]
    assert data["tv_libraries"] == ["/data/tv"]


def test_infer_saved_operating_mode(
    tmp_path: Path,
):
    path = make_config_file(tmp_path)

    apply_operating_mode(
        path,
        get_operating_mode("home_port"),
    )

    config = make_config(
        path,
        profile="normal",
        read_only=False,
    )

    assert (
        infer_operating_mode(config).key
        == "home_port"
    )


def test_legacy_ship_offline_maps_to_underway(
    tmp_path: Path,
):
    path = make_config_file(tmp_path)

    data = json.loads(
        path.read_text(encoding="utf-8")
    )
    data.pop("operating_mode", None)
    path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    config = make_config(
        path,
        profile="ship_offline",
    )

    assert infer_operating_mode(config).key == "underway"
