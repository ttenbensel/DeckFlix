from pathlib import Path
from types import SimpleNamespace

from deckflix_app.decision import ApprovalStatus
from deckflix_app.home_screen import (
    mode_name,
    path_status,
    recommended_action,
    show_home_screen,
)
from deckflix_app.operation import (
    OperationManager,
    approve_ready_items,
    prepare_operation,
)


def make_config(
    tmp_path: Path,
    *,
    read_only: bool = True,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    config_path = tmp_path / "local.json"
    config_path.write_text(
        '{"operating_mode": "passage"}',
        encoding="utf-8",
    )

    return SimpleNamespace(
        shuttle=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        read_only=read_only,
        operating_profile="ship_limited",
        low_impact=True,
        source_path=config_path,
        network=SimpleNamespace(
            allow_metadata_downloads=False,
            allow_jellyfin_refresh=True,
            max_download_mbps=5,
        ),
    )


def make_operation(
    tmp_path: Path,
    *,
    read_only: bool = True,
):
    config = make_config(
        tmp_path,
        read_only=read_only,
    )

    source = (
        config.shuttle
        / "Alien (1979)"
        / "Alien.1979.1080p.BluRay.HEVC.mkv"
    )
    source.parent.mkdir()
    source.write_bytes(b"media")

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=config.shuttle,
        movie_libraries=config.movie_libraries,
        tv_libraries=config.tv_libraries,
        operation_id="DF-HOME-001",
    )

    return config, manager


def test_path_status(tmp_path: Path):
    path = tmp_path / "library"

    assert path_status(path) == "OFFLINE"

    path.mkdir()

    assert path_status(path) == "ONLINE"


def test_mode_name():
    assert mode_name(True) == "SAFE MODE"
    assert mode_name(False) == "IMPORT MODE"


def test_no_operation_recommends_begin():
    manager = OperationManager()

    assert recommended_action(
        manager,
        read_only=True,
    ) == "Begin Shuttle Operation"


def test_snapshot_ready_recommends_approval(
    tmp_path: Path,
):
    _, manager = make_operation(tmp_path)

    assert manager.approval_plan.count(
        ApprovalStatus.READY
    ) == 1

    assert "Review and Approve" in recommended_action(
        manager,
        read_only=True,
    )


def test_approved_safe_mode_recommends_disable(
    tmp_path: Path,
):
    _, manager = make_operation(tmp_path)

    approve_ready_items(manager)

    assert recommended_action(
        manager,
        read_only=True,
    ) == "Unlock Library to Begin Import"


def test_approved_import_mode_recommends_execute(
    tmp_path: Path,
):
    _, manager = make_operation(
        tmp_path,
        read_only=False,
    )

    approve_ready_items(manager)

    assert recommended_action(
        manager,
        read_only=False,
    ) == "Execute Approved Import"


def test_home_screen_shows_system_state(
    tmp_path: Path,
    capsys,
):
    config = make_config(tmp_path)

    show_home_screen(
        app_name="DeckFlix",
        version="0.8.0",
        codename="Safe Repair Preview",
        config=config,
        operation_manager=OperationManager(),
    )

    output = capsys.readouterr().out

    assert "DECKFLIX" in output
    assert "Connected" in output
    assert "2/2" in output
    assert "Passage" in output
    assert "Protection" in output
    assert "Enabled" in output
    assert "No active operation" in output
    assert "Begin Shuttle Operation" in output


def test_home_screen_shows_active_operation(
    tmp_path: Path,
    capsys,
):
    config, manager = make_operation(tmp_path)

    show_home_screen(
        app_name="DeckFlix",
        version="0.8.0",
        codename="Safe Repair Preview",
        config=config,
        operation_manager=manager,
    )

    output = capsys.readouterr().out

    assert "DF-HOME-001" in output
    assert "SNAPSHOT_READY" in output
    assert "Snapshot    VALID" in output
    assert "Files       1" in output
    assert "Ready       1" in output
    assert "Recommended Next Action" in output
