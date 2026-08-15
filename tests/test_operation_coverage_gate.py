from pathlib import Path

from deckflix_app.operation import (
    OperationManager,
    OperationState,
    SnapshotDisposition,
    approve_ready_items,
    execute_operation,
    prepare_operation,
)


def test_operation_stays_approved_when_snapshot_unresolved(
    tmp_path: Path,
):
    shuttle = (
        tmp_path
        / "shuttle"
    )

    movies = (
        tmp_path
        / "movies"
    )

    tv = (
        tmp_path
        / "tv"
    )

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    new_movie = (
        shuttle
        / "Alien (1979)"
        / "Alien.1979.1080p.BluRay.HEVC.mkv"
    )

    new_movie.parent.mkdir()
    new_movie.write_bytes(
        b"alien"
    )

    review_movie = (
        shuttle
        / "Avatar (2009)"
        / "Avatar.2009.2160p.BluRay.HEVC.mkv"
    )

    review_movie.parent.mkdir()
    review_movie.write_bytes(
        b"incoming-avatar"
    )

    existing = (
        movies
        / "Avatar (2009)"
        / "Avatar.2009.1080p.WEB-DL.x264.mkv"
    )

    existing.parent.mkdir()
    existing.write_bytes(
        b"existing-avatar"
    )

    manager = (
        OperationManager()
    )

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[
            movies
        ],
        tv_libraries=[
            tv
        ],
        operation_id=(
            "DF-COVERAGE-001"
        ),
    )

    approved = (
        approve_ready_items(
            manager
        )
    )

    assert approved == 1

    manager.authorize_import()

    certificate = (
        execute_operation(
            manager,
            movie_library=movies,
            tv_library=tv,
            temp_dir=(
                tmp_path
                / "temp"
            ),
            read_only=False,
        )
    )

    assert certificate is not None

    assert (
        certificate.import_result.completed
        == 1
    )

    assert (
        certificate.safety.safe
        is False
    )

    assert (
        certificate.safety.snapshot_unresolved
        == 1
    )

    assert (
        manager.state
        is OperationState.APPROVED
    )

    ledger = (
        manager.require_ledger()
    )

    imported_entry = ledger.get(
        new_movie.relative_to(
            shuttle
        )
    )

    review_entry = ledger.get(
        review_movie.relative_to(
            shuttle
        )
    )

    assert (
        imported_entry.disposition
        is SnapshotDisposition.IMPORTED
    )

    assert (
        review_entry.disposition
        is SnapshotDisposition.UNRESOLVED
    )
