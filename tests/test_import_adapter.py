from pathlib import Path

import pytest

from deckflix_app.decision import Action
from deckflix_app.importer import (
    import_job_from_plan_item,
    queue_from_legacy_plan,
)
from deckflix_app.media import MediaInfo


def make_media(path: Path) -> MediaInfo:
    return MediaInfo(
        path=path,
        media_type="movie",
        title="Test Movie",
        year=2026,
        season=None,
        episode=None,
        resolution="1080p",
        source="BluRay",
        codec="HEVC",
        quality_score=70,
    )


def make_plan_item(
    source: Path,
    target: Path,
    *,
    status: str = "READY",
) -> dict:
    return {
        "media": make_media(source),
        "source": source,
        "target": target,
        "status": status,
    }


def test_adapter_builds_typed_import_job(tmp_path: Path):
    source = tmp_path / "shuttle" / "movie.mkv"
    target = tmp_path / "library" / "movie.mkv"

    source.parent.mkdir()
    source.write_bytes(b"media")

    job = import_job_from_plan_item(
        make_plan_item(source, target)
    )

    assert job.source == source
    assert job.destination == target
    assert job.decision.action is Action.NEW
    assert job.decision.existing_score == 0
    assert job.decision.incoming_score == 70
    assert job.completed is False
    assert job.copied is False
    assert job.verified is False


def test_adapter_rejects_non_ready_item(tmp_path: Path):
    source = tmp_path / "movie.mkv"
    target = tmp_path / "library" / "movie.mkv"

    with pytest.raises(ValueError, match="not ready"):
        import_job_from_plan_item(
            make_plan_item(
                source,
                target,
                status="REVIEW",
            )
        )


def test_adapter_rejects_existing_destination(tmp_path: Path):
    source = tmp_path / "movie.mkv"
    target = tmp_path / "library" / "movie.mkv"

    target.parent.mkdir()
    target.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        import_job_from_plan_item(
            make_plan_item(source, target)
        )


def test_queue_adapter_skips_existing_plan_items(
    tmp_path: Path,
):
    ready_source = tmp_path / "ready.mkv"
    ready_target = tmp_path / "library" / "ready.mkv"

    skipped_source = tmp_path / "skipped.mkv"
    skipped_target = tmp_path / "library" / "skipped.mkv"

    queue = queue_from_legacy_plan(
        [
            make_plan_item(
                ready_source,
                ready_target,
                status="READY",
            ),
            make_plan_item(
                skipped_source,
                skipped_target,
                status="SKIP_EXISTS",
            ),
        ]
    )

    assert len(queue.jobs) == 1
    assert queue.jobs[0].source == ready_source
    assert queue.jobs[0].destination == ready_target


def test_queue_adapter_rejects_unknown_status(
    tmp_path: Path,
):
    source = tmp_path / "movie.mkv"
    target = tmp_path / "library" / "movie.mkv"

    with pytest.raises(ValueError, match="not ready"):
        queue_from_legacy_plan(
            [
                make_plan_item(
                    source,
                    target,
                    status="UNKNOWN",
                )
            ]
        )
