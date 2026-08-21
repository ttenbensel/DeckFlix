from pathlib import Path

from typing import cast

from deckflix_app.decision import Decision
from deckflix_app.importer import ImportEngine, ImportJob, ImportQueue


def make_decision() -> Decision:
    """
    The import engine carries the decision with the job but does not
    interpret it. Decision behaviour is covered by the decision tests.
    """
    return cast(Decision, object())


def test_engine_imports_and_verifies_file(tmp_path: Path):
    source = tmp_path / "source.mkv"
    destination = tmp_path / "library" / "source.mkv"
    temp_dir = tmp_path / "temporary"

    source.write_bytes(b"deckflix test media")

    queue = ImportQueue()
    job = ImportJob(
        source=source,
        destination=destination,
        decision=make_decision(),
    )
    queue.add(job)

    result = ImportEngine().execute(queue, temp_dir)

    assert result.total == 1
    assert result.completed == 1
    assert result.failed == 0
    assert result.failures == []
    assert result.successful is True
    assert result.safe_to_empty is True

    assert job.copied is True
    assert job.verified is True
    assert job.completed is True

    assert destination.read_bytes() == b"deckflix test media"
    assert queue.pending() == []
    assert queue.completed() == [job]


def test_engine_reports_failed_job(tmp_path: Path):
    source = tmp_path / "missing.mkv"
    destination = tmp_path / "library" / "missing.mkv"
    temp_dir = tmp_path / "temporary"

    queue = ImportQueue()
    job = ImportJob(
        source=source,
        destination=destination,
        decision=make_decision(),
    )
    queue.add(job)

    result = ImportEngine().execute(queue, temp_dir)

    assert result.total == 1
    assert result.completed == 0
    assert result.failed == 1
    assert result.successful is False
    assert result.safe_to_empty is False

    assert len(result.failures) == 1
    assert result.failures[0].job is job
    assert result.failures[0].message

    assert job.copied is False
    assert job.verified is False
    assert job.completed is False
    assert queue.pending() == [job]


def test_empty_queue_is_not_safe_to_empty(tmp_path: Path):
    queue = ImportQueue()

    result = ImportEngine().execute(queue, tmp_path / "temporary")

    assert result.total == 0
    assert result.completed == 0
    assert result.failed == 0
    assert result.successful is False
    assert result.safe_to_empty is False


def test_upgrade_retires_old_file_only_after_verified_install(
    tmp_path: Path,
):
    source = tmp_path / "shuttle" / "episode.mp4"
    old = tmp_path / "library" / "episode.mkv"
    destination = (
        tmp_path / "library" / "episode.mp4"
    )
    temp_dir = tmp_path / "temporary"

    source.parent.mkdir()
    old.parent.mkdir()

    source.write_bytes(b"better-media")
    old.write_bytes(b"inferior-media")

    queue = ImportQueue()
    job = ImportJob(
        source=source,
        destination=destination,
        decision=make_decision(),
        replace_path=old,
    )
    queue.add(job)

    result = ImportEngine().execute(
        queue,
        temp_dir,
    )

    assert result.completed == 1
    assert result.failed == 0

    assert destination.exists()
    assert (
        destination.read_bytes()
        == b"better-media"
    )

    assert not old.exists()
    assert source.exists()

    assert job.copied is True
    assert job.verified is True
    assert job.completed is True


def test_failed_upgrade_preserves_old_library_file(
    tmp_path: Path,
):
    source = tmp_path / "shuttle" / "missing.mp4"
    old = tmp_path / "library" / "episode.mkv"
    destination = (
        tmp_path / "library" / "episode.mp4"
    )

    old.parent.mkdir()
    old.write_bytes(b"inferior-but-safe")

    queue = ImportQueue()
    job = ImportJob(
        source=source,
        destination=destination,
        decision=make_decision(),
        replace_path=old,
    )
    queue.add(job)

    result = ImportEngine().execute(
        queue,
        tmp_path / "temporary",
    )

    assert result.completed == 0
    assert result.failed == 1

    assert old.exists()
    assert (
        old.read_bytes()
        == b"inferior-but-safe"
    )
    assert not destination.exists()
