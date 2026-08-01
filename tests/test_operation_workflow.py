from pathlib import Path

from deckflix_app.decision import ApprovalStatus
from deckflix_app.operation import (
    OperationManager,
    OperationState,
    prepare_operation,
)


def test_prepare_operation_attaches_workflow_data(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    incoming = (
        shuttle
        / "1883"
        / "1883.S01E01.1080p.WEB-DL.HEVC.mkv"
    )
    incoming.parent.mkdir()
    incoming.write_bytes(b"incoming media")

    manager = OperationManager()

    operation = prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        operation_id="DF-WORKFLOW-001",
    )

    assert operation.id == "DF-WORKFLOW-001"
    assert operation.state is OperationState.SNAPSHOT_READY
    assert operation.snapshot.file_count == 1

    assert manager.decisions is not None
    assert manager.decisions.total == 1

    assert manager.approval_plan is not None
    assert manager.approval_plan.total == 1
    assert (
        manager.approval_plan.count(
            ApprovalStatus.READY
        )
        == 1
    )


def test_prepare_operation_detects_existing_episode(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    incoming = (
        shuttle
        / "1883"
        / "1883.S01E01.1080p.WEB-DL.HEVC.mkv"
    )
    existing = (
        tv
        / "1883"
        / "Season 01"
        / "1883.S01E01.1080p.WEB-DL.HEVC.mkv"
    )

    incoming.parent.mkdir()
    existing.parent.mkdir(parents=True)

    incoming.write_bytes(b"incoming")
    existing.write_bytes(b"existing")

    manager = OperationManager()

    prepare_operation(
        manager,
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
    )

    assert manager.approval_plan.total == 1
    assert (
        manager.approval_plan.count(
            ApprovalStatus.SKIPPED
        )
        == 1
    )
