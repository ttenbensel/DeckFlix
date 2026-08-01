from pathlib import Path

from deckflix_app.screens.shuttle import show_receive_shuttle


def test_receive_shuttle_reports_missing_drive(
    tmp_path: Path,
    capsys,
):
    shuttle = tmp_path / "missing-shuttle"
    movies = tmp_path / "movies"
    movies.mkdir()

    show_receive_shuttle(
        shuttle_path=shuttle,
        movie_library_path=movies,
    )

    output = capsys.readouterr().out

    assert "Receive Shuttle" in output
    assert "Not Found" in output
    assert "Shuttle scan cancelled" in output
    assert "Nothing has been changed" in output


def test_receive_shuttle_reports_empty_drive(
    tmp_path: Path,
    capsys,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"

    shuttle.mkdir()
    movies.mkdir()

    show_receive_shuttle(
        shuttle_path=shuttle,
        movie_library_path=movies,
    )

    output = capsys.readouterr().out

    assert "Connected" in output
    assert "Video files          0" in output
    assert "No shuttle media found" in output
    assert "Nothing has been changed" in output
