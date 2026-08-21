from pathlib import Path
from typing import cast

from deckflix_app.decision import Decision
from deckflix_app.importer import (
    ImportJob,
    ImportQueue,
    ResumableImportExecutor,
)


def make_decision() -> Decision:
    return cast(Decision, object())


def test_resume_retires_old_upgrade_after_destination_installed(
    tmp_path: Path,
):
    source = tmp_path / "shuttle" / "episode.mp4"
    destination = (
        tmp_path / "library" / "episode.mp4"
    )
    old = tmp_path / "library" / "episode.mkv"

    source.parent.mkdir()
    destination.parent.mkdir()

    payload = b"verified-new-media"

    source.write_bytes(payload)
    destination.write_bytes(payload)
    old.write_bytes(b"old-media")

    queue = ImportQueue()
    job = ImportJob(
        source=source,
        destination=destination,
        decision=make_decision(),
        replace_path=old,
    )
    queue.add(job)

    result = ResumableImportExecutor().execute(
        operation_id="DF-UPGRADE-RESUME",
        queue=queue,
        temp_dir=tmp_path / "temp",
        journal_path=tmp_path / "journal.json",
    )

    assert result.completed == 1
    assert result.failed == 0

    assert destination.read_bytes() == payload
    assert not old.exists()

    assert job.copied is True
    assert job.verified is True
    assert job.completed is True
