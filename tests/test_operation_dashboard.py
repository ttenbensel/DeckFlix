from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    prepare_operation,
)
from deckflix_app.screens.operation_dashboard import (
    show_operation_dashboard,
)


def test_dashboard_reports_no_active_operation(capsys):
    manager = OperationManager()

    show_operation_dashboard(manager)

    output = capsys.readouterr().out

    assert "No operation is active" in output


def test_dashboard_shows_active_operation(
    tmp_path: Path,
    capsys,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    (shuttle / "movie.mkv").write_bytes(b"media")

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-DASH-001",
    )

    show_operation_dashboard(manager)

    output = capsys.readouterr().out

    assert "DF-DASH-001" in output
    assert "SNAPSHOT_READY" in output
    assert "Snapshot status    VALID" in output
    assert "Files              1" in output
    assert "Decision Queue" in output
    assert "Approval Plan" in output
