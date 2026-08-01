from datetime import datetime
from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    approve_ready_items,
    execute_operation,
    list_history_records,
    prepare_operation,
)


def test_completed_operation_saves_history(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"
    temp = tmp_path / "temp"
    history = tmp_path / "history"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    source = (
        shuttle
        / "Alien (1979)"
        / "Alien.1979.1080p.BluRay.HEVC.mkv"
    )
    source.parent.mkdir()
    source.write_bytes(b"alien")

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-HISTORY-001",
    )

    approve_ready_items(manager)
    manager.authorize_import()

    certificate = execute_operation(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=temp,
        read_only=False,
        history_directory=history,
    )

    assert certificate is not None

    records = list_history_records(history)

    assert len(records) == 1
    assert records[0].operation_id == "DF-HISTORY-001"
    assert records[0].snapshot_files == 1
    assert records[0].imported == 1
    assert records[0].failed == 0
    assert records[0].safe_to_empty is True
    assert records[0].trust_score == 100


def test_read_only_operation_writes_no_history(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"
    history = tmp_path / "history"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    source = shuttle / "movie.mkv"
    source.write_bytes(b"media")

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
    )

    approve_ready_items(manager)

    result = execute_operation(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=tmp_path / "temp",
        read_only=True,
        history_directory=history,
    )

    assert result is None
    assert list_history_records(history) == []
