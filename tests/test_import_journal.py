from pathlib import Path

import pytest

from deckflix_app.decision import (
    Action,
    Decision,
)
from deckflix_app.importer import (
    ImportJob,
    ImportQueue,
    ImportStage,
    ResumableImportExecutor,
    load_import_journal,
)


def make_job(
    source: Path,
    destination: Path,
) -> ImportJob:
    return ImportJob(
        source=source,
        destination=destination,
        decision=Decision(
            action=Action.NEW,
            reason="Resume test",
            existing_score=0,
            incoming_score=100,
        ),
    )


def make_queue(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    library = tmp_path / "library"

    shuttle.mkdir()
    library.mkdir()

    queue = ImportQueue()
    jobs = []

    for number in range(1, 4):
        source = shuttle / f"file-{number}.mkv"
        destination = library / f"file-{number}.mkv"

        source.write_bytes(
            f"media-{number}".encode()
        )

        job = make_job(
            source,
            destination,
        )
        jobs.append(job)
        queue.add(job)

    return queue, jobs, library


def test_journal_records_completed_files(
    tmp_path: Path,
):
    queue, _, _ = make_queue(tmp_path)
    journal_path = tmp_path / "journal.json"

    result = ResumableImportExecutor().execute(
        operation_id="DF-JOURNAL-001",
        queue=queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        delete_journal_when_complete=False,
    )

    journal = load_import_journal(journal_path)

    assert result.completed == 3
    assert journal is not None
    assert journal.completed == 3
    assert journal.failed == 0
    assert journal.pending == 0


def test_interrupted_import_resumes_without_duplicate_copy(
    tmp_path: Path,
):
    queue, jobs, library = make_queue(tmp_path)
    journal_path = tmp_path / "journal.json"

    completed_events = 0

    def interrupt_after_first_completion(event):
        nonlocal completed_events

        if event.stage is ImportStage.COMPLETED:
            completed_events += 1

            if completed_events == 1:
                raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        ResumableImportExecutor().execute(
            operation_id="DF-RESUME-001",
            queue=queue,
            temp_dir=tmp_path / "temp",
            journal_path=journal_path,
            progress=interrupt_after_first_completion,
            delete_journal_when_complete=False,
        )

    assert (library / "file-1.mkv").exists()

    resumed_queue = ImportQueue()

    for job in jobs:
        resumed_queue.add(
            make_job(
                job.source,
                job.destination,
            )
        )

    events = []

    result = ResumableImportExecutor().execute(
        operation_id="DF-RESUME-001",
        queue=resumed_queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        progress=events.append,
        delete_journal_when_complete=False,
    )

    assert result.completed == 3
    assert result.failed == 0

    assert any(
        event.stage is ImportStage.RESUMED
        for event in events
    )

    for number in range(1, 4):
        assert (
            library / f"file-{number}.mkv"
        ).read_bytes() == (
            f"media-{number}".encode()
        )


def test_resume_rejects_conflicting_destination(
    tmp_path: Path,
):
    queue, jobs, library = make_queue(tmp_path)
    journal_path = tmp_path / "journal.json"

    conflicting = library / "file-1.mkv"
    conflicting.write_bytes(b"wrong content")

    result = ResumableImportExecutor().execute(
        operation_id="DF-CONFLICT-001",
        queue=queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        delete_journal_when_complete=False,
    )

    assert result.failed == 1
    assert result.completed == 2
    assert conflicting.read_bytes() == b"wrong content"
