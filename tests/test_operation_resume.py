from pathlib import Path

import pytest

from deckflix_app.importer import ImportStage
from deckflix_app.operation import (
    OperationManager,
    approve_ready_items,
    execute_operation,
    prepare_operation,
)


def test_operation_resumes_after_interruption(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"
    temp = tmp_path / "temp"
    journal = tmp_path / "journal.json"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    for title, year in [
        ("Alien", 1979),
        ("Avatar", 2009),
    ]:
        source = (
            shuttle
            / f"{title} ({year})"
            / f"{title}.{year}.1080p.BluRay.HEVC.mkv"
        )
        source.parent.mkdir()
        source.write_bytes(
            title.encode()
        )

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-OP-RESUME-001",
    )

    approve_ready_items(manager)

    completed = 0

    def stop_after_first(event):
        nonlocal completed

        if event.stage is ImportStage.COMPLETED:
            completed += 1

            if completed == 1:
                raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execute_operation(
            manager,
            movie_library=movies,
            tv_library=tv,
            temp_dir=temp,
            read_only=False,
            progress=stop_after_first,
            journal_path=journal,
        )

    # Simulate restoring an interrupted operation.
    manager.operation = manager.operation.__class__(
        id=manager.operation.id,
        state=manager.operation.state.__class__.APPROVED,
        snapshot=manager.operation.snapshot,
        created_at=manager.operation.created_at,
    )

    certificate = execute_operation(
        manager,
        movie_library=movies,
        tv_library=tv,
        temp_dir=temp,
        read_only=False,
        journal_path=journal,
    )

    assert certificate is not None
    assert manager.import_result.completed == 2
    assert manager.import_result.failed == 0
    assert certificate.safety.safe is True
