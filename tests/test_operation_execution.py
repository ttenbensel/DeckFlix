from pathlib import Path

import pytest

from deckflix_app.decision import ApprovalStatus
from deckflix_app.operation import (
    OperationManager,
    OperationState,
    approve_ready_items,
    build_operation_import_queue,
    destination_for_media,
    execute_operation,
    prepare_operation,
)


def prepare_new_movie(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    source = (
        shuttle
        / "Alien (1979)"
        / "Alien.1979.1080p.BluRay.HEVC.mkv"
    )
    source.parent.mkdir()
    source.write_bytes(b"alien media")

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-EXEC-001",
    )

    return manager, source, movies, tv


def test_approve_ready_items(tmp_path: Path):
    manager, _, _, _ = prepare_new_movie(tmp_path)

    approved = approve_ready_items(manager)

    assert approved == 1
    assert manager.state is OperationState.APPROVED
    assert (
        manager.approval_plan.count(
            ApprovalStatus.APPROVED
        )
        == 1
    )


def test_build_queue_from_approved_operation(
    tmp_path: Path,
):
    manager, source, movies, tv = prepare_new_movie(
        tmp_path
    )
    approve_ready_items(manager)

    queue = build_operation_import_queue(
        manager,
        movie_library=movies,
        tv_library=tv,
    )

    assert len(queue.jobs) == 1
    assert queue.jobs[0].source == source
    assert queue.jobs[0].destination == (
        movies
        / "Alien (1979)"
        / source.name
    )


def test_read_only_execution_changes_nothing(
    tmp_path: Path,
):
    manager, source, movies, tv = prepare_new_movie(
        tmp_path
    )
    approve_ready_items(manager)
    manager.authorize_import()

    certificate = execute_operation(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=tmp_path / "temp",
        read_only=True,
    )

    assert certificate is None
    assert manager.state is OperationState.APPROVED
    assert source.exists()
    assert list(movies.rglob("*.mkv")) == []


def test_execute_approved_operation(tmp_path: Path):
    manager, source, movies, tv = prepare_new_movie(
        tmp_path
    )
    approve_ready_items(manager)
    manager.authorize_import()

    certificate = execute_operation(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=tmp_path / "temp",
        read_only=False,
    )

    destination = (
        movies
        / "Alien (1979)"
        / source.name
    )

    assert certificate is not None
    assert destination.exists()
    assert destination.read_bytes() == b"alien media"
    assert manager.state is OperationState.COMPLETE
    assert manager.import_result.completed == 1


def test_destination_for_tv_episode(tmp_path: Path):
    manager, _, movies, tv = prepare_new_movie(tmp_path)
    media = manager.decisions.items[0].incoming

    media.media_type = "tv"
    media.title = "1883"
    media.season = 1
    media.episode = 1

    destination = destination_for_media(
        media,
        movie_library=movies,
        tv_library=tv,
    )

    assert destination.parent == (
        tv / "1883" / "Season 01"
    )
