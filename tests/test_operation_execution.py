from pathlib import Path

import pytest

from deckflix_app.decision import ApprovalStatus
from deckflix_app.operation import (
    InvalidOperationTransition,
    OperationManager,
    OperationState,
    SnapshotDisposition,
    approve_ready_items,
    build_operation_import_queue,
    destination_for_media,
    execute_operation,
    prepare_operation,
    record_imported_jobs,
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


def test_execute_approved_operation_records_ledger(
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

    relative = source.relative_to(
        manager.operation.snapshot.shuttle_path
    )

    entry = manager.require_ledger().get(relative)

    assert entry is not None

    assert (
        entry.disposition
        is SnapshotDisposition.IMPORTED
    )

    assert entry.evidence_path == destination.resolve()
    assert entry.sha256 is not None
    assert len(entry.sha256) == 64

    assert manager.require_ledger().accounted_files == 1
    assert manager.require_ledger().unresolved_files == 0


def test_record_imported_jobs_rejects_incomplete_job(
    tmp_path: Path,
):
    manager, _, movies, tv = prepare_new_movie(
        tmp_path
    )

    approve_ready_items(manager)

    queue = build_operation_import_queue(
        manager,
        movie_library=movies,
        tv_library=tv,
    )

    with pytest.raises(
        InvalidOperationTransition,
        match="incomplete import job",
    ):
        record_imported_jobs(
            manager,
            queue,
        )


def test_record_imported_jobs_rejects_missing_destination(
    tmp_path: Path,
):
    manager, _, movies, tv = prepare_new_movie(
        tmp_path
    )

    approve_ready_items(manager)

    queue = build_operation_import_queue(
        manager,
        movie_library=movies,
        tv_library=tv,
    )

    job = queue.jobs[0]

    job.copied = True
    job.verified = True
    job.completed = True

    with pytest.raises(
        InvalidOperationTransition,
        match="destination is missing",
    ):
        record_imported_jobs(
            manager,
            queue,
        )


def test_destination_for_tv_episode(
    tmp_path: Path,
):
    manager, _, movies, tv = prepare_new_movie(
        tmp_path
    )

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
        tv
        / "1883"
        / "Season 01"
    )

def test_execute_operation_rejects_stale_destination_before_import(
    tmp_path,
):
    """
    An approved NEW item may become stale if its destination
    appears after approval but before execution.

    Execution must fail closed before entering IMPORTING and
    must preserve the existing destination byte-for-byte.
    """
    from deckflix_app.decision import (
        ApprovalStatus,
    )
    from deckflix_app.operation import (
        OperationState,
        execute_operation,
    )

    manager, source, movie_library, tv_library = (
        prepare_new_movie(
            tmp_path
        )
    )

    approve_ready_items(
        manager
    )

    approved = manager.approval_plan.approved()

    assert len(approved) == 1
    assert (
        approved[0].status
        is ApprovalStatus.APPROVED
    )

    media = approved[0].queue_item.incoming

    destination = destination_for_media(
        media,
        movie_library=movie_library,
        tv_library=tv_library,
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    destination.write_bytes(
        b"existing-library-content"
    )

    before = destination.read_bytes()

    import pytest

    with pytest.raises(
        Exception,
        match="destination conflict",
    ):
        execute_operation(
            manager,
            movie_library=movie_library,
            tv_library=tv_library,
            temp_dir=tmp_path / "temp",
            read_only=False,
        )

    assert (
        manager.state
        is OperationState.APPROVED
    )
    assert destination.read_bytes() == before
    assert source.exists()

