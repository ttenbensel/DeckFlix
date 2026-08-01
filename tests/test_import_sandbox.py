from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    OperationState,
    approve_ready_items,
    execute_operation,
    prepare_operation,
)


def test_complete_sandbox_import_operation(
    tmp_path: Path,
):
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
        b"sandbox movie"
    )
    episode.write_bytes(
        b"sandbox episode"
    )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-SANDBOX-001",
    )

    assert manager.state is (
        OperationState.SNAPSHOT_READY
    )
    assert manager.decisions.total == 2

    approved = approve_ready_items(
        manager
    )

    assert approved == 2
    assert manager.state is (
        OperationState.APPROVED
    )

    manager.authorize_import()

    events = []

    certificate = execute_operation(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=temp,
        read_only=False,
        progress=events.append,
    )

    assert certificate is not None
    assert certificate.safety.safe is True
    assert certificate.trust_score == 100

    assert manager.state is (
        OperationState.COMPLETE
    )
    assert manager.import_result.total == 2
    assert manager.import_result.completed == 2
    assert manager.import_result.failed == 0

    movie_destination = (
        movies
        / "Alien (1979)"
        / movie.name
    )

    episode_destination = (
        tv
        / "1883"
        / "Season 01"
        / episode.name
    )

    assert movie_destination.read_bytes() == (
        b"sandbox movie"
    )
    assert episode_destination.read_bytes() == (
        b"sandbox episode"
    )

    assert movie.exists()
    assert episode.exists()

    assert not any(
        path.is_file()
        for path in temp.rglob("*")
    )
