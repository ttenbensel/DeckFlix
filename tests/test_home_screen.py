from pathlib import Path
from types import SimpleNamespace

from deckflix_app.home_screen import (
    mode_name,
    path_status,
    show_home_screen,
)


def make_config(tmp_path: Path, *, read_only: bool = True):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    return SimpleNamespace(
        shuttle=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        read_only=read_only,
        operating_profile="ship_limited",
        low_impact=True,
    )


def test_path_status(tmp_path: Path):
    path = tmp_path / "library"

    assert path_status(path) == "OFFLINE"

    path.mkdir()

    assert path_status(path) == "ONLINE"


def test_mode_name():
    assert mode_name(True) == "SAFE MODE"
    assert mode_name(False) == "IMPORT MODE"


def test_home_screen_shows_system_state(
    tmp_path: Path,
    capsys,
):
    config = make_config(tmp_path)

    show_home_screen(
        app_name="DeckFlix",
        version="0.6.0",
        codename="Trust",
        config=config,
    )

    output = capsys.readouterr().out

    assert "DECKFLIX" in output
    assert "Connected" in output
    assert "2/2" in output
    assert "SAFE MODE" in output
    assert "ship_limited" in output
    assert "Enabled" in output
    assert "0.6.0" in output
    assert "Trust" in output
