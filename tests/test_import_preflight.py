from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    approve_ready_items,
    prepare_operation,
    run_import_preflight,
)


def prepare_manager(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"
    temp = tmp_path / "temp"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    movie = (
        shuttle
        / "Alien (1979)"
        / "Alien.1979.1080p.BluRay.HEVC.mkv"
    )

    episode = (
        shuttle
        / "1883"
        / "1883.S01E01.1080p.WEB-DL.HEVC.mkv"
    )

    movie.parent.mkdir()
    episode.parent.mkdir()

    movie.write_bytes(
        b"movie data"
    )
    episode.write_bytes(
        b"episode data"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-PREFLIGHT-001",
    )

    approve_ready_items(manager)

    return (
        manager,
        movie,
        episode,
        movies,
        tv,
        temp,
    )


def test_ready_preflight_passes(
    tmp_path: Path,
):
    (
        manager,
        _,
        _,
        movies,
        tv,
        temp,
    ) = prepare_manager(tmp_path)

    result = run_import_preflight(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=temp,
    )

    assert result.ready is True
    assert result.approved_files == 2
    assert result.approved_bytes == 22
    assert result.movie_bytes == 10
    assert result.tv_bytes == 12
    assert result.missing_sources == []
    assert result.changed_sources == []
    assert result.conflicts == []
    assert result.errors == []


def test_preflight_detects_destination_conflict(
    tmp_path: Path,
):
    (
        manager,
        movie,
        _,
        movies,
        tv,
        temp,
    ) = prepare_manager(tmp_path)

    destination = (
        movies
        / "Alien (1979)"
        / movie.name
    )

    destination.parent.mkdir(
        parents=True
    )
    destination.write_bytes(
        b"existing"
    )

    result = run_import_preflight(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=temp,
    )

    assert result.ready is False
    assert len(result.conflicts) == 1
    assert (
        result.conflicts[0].destination
        == destination
    )


def test_preflight_detects_changed_source(
    tmp_path: Path,
):
    (
        manager,
        movie,
        _,
        movies,
        tv,
        temp,
    ) = prepare_manager(tmp_path)

    movie.write_bytes(
        b"changed movie data"
    )

    result = run_import_preflight(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=temp,
    )

    assert result.ready is False
    assert result.snapshot_valid is False


def test_preflight_requires_approved_items(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    (shuttle / "movie.mkv").write_bytes(
        b"media"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
    )

    result = run_import_preflight(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=tmp_path / "temp",
    )

    assert result.ready is False
    assert result.approved_files == 0
