from pathlib import Path

import pytest

from deckflix_app.decision import Action, Decision
from deckflix_app.importer import (
    ImportJob,
    ImportQueue,
    ImportStage,
    JournalStatus,
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
            reason="Reliability test",
            existing_score=0,
            incoming_score=100,
        ),
    )


def make_single_job(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    library = tmp_path / "library"

    shuttle.mkdir()
    library.mkdir()

    source = shuttle / "movie.mkv"
    destination = library / "movie.mkv"

    source.write_bytes(b"verified media data")

    queue = ImportQueue()
    queue.add(make_job(source, destination))

    return queue, source, destination


def test_full_disk_failure_is_journalled(
    tmp_path: Path,
    monkeypatch,
):
    queue, source, destination = make_single_job(tmp_path)
    journal_path = tmp_path / "journal.json"

    def disk_full(*args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(
        "deckflix_app.importer.engine.copy_job",
        disk_full,
    )

    result = ResumableImportExecutor().execute(
        operation_id="DF-DISK-FULL-001",
        queue=queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        delete_journal_when_complete=False,
    )

    journal = load_import_journal(journal_path)
    entry = next(iter(journal.entries.values()))

    assert result.completed == 0
    assert result.failed == 1
    assert entry.status is JournalStatus.FAILED
    assert "No space left on device" in entry.error

    assert source.exists()
    assert destination.exists() is False


def test_atomic_move_failure_does_not_create_library_file(
    tmp_path: Path,
    monkeypatch,
):
    queue, source, destination = make_single_job(tmp_path)
    journal_path = tmp_path / "journal.json"

    def move_failure(*args, **kwargs):
        raise PermissionError(
            "Destination became read-only"
        )

    monkeypatch.setattr(
        "deckflix_app.importer.engine.atomic_move",
        move_failure,
    )

    result = ResumableImportExecutor().execute(
        operation_id="DF-MOVE-FAIL-001",
        queue=queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        delete_journal_when_complete=False,
    )

    journal = load_import_journal(journal_path)
    entry = next(iter(journal.entries.values()))

    assert result.completed == 0
    assert result.failed == 1
    assert entry.status is JournalStatus.FAILED
    assert "read-only" in entry.error

    assert source.exists()
    assert destination.exists() is False


def test_failed_job_retries_after_problem_is_fixed(
    tmp_path: Path,
    monkeypatch,
):
    queue, source, destination = make_single_job(tmp_path)
    journal_path = tmp_path / "journal.json"

    original_copy = __import__(
        "deckflix_app.importer.engine",
        fromlist=["copy_job"],
    ).copy_job

    attempts = 0

    def fail_once(job, temp_dir):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            raise OSError("Temporary storage unavailable")

        return original_copy(job, temp_dir)

    monkeypatch.setattr(
        "deckflix_app.importer.engine.copy_job",
        fail_once,
    )

    first = ResumableImportExecutor().execute(
        operation_id="DF-RETRY-001",
        queue=queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        delete_journal_when_complete=False,
    )

    assert first.failed == 1
    assert destination.exists() is False

    retry_queue = ImportQueue()
    retry_queue.add(make_job(source, destination))

    second = ResumableImportExecutor().execute(
        operation_id="DF-RETRY-001",
        queue=retry_queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        delete_journal_when_complete=False,
    )

    journal = load_import_journal(journal_path)
    entry = next(iter(journal.entries.values()))

    assert second.completed == 1
    assert second.failed == 0
    assert entry.status is JournalStatus.COMPLETED
    assert destination.read_bytes() == b"verified media data"


def test_removed_shuttle_file_fails_without_corrupting_library(
    tmp_path: Path,
):
    queue, source, destination = make_single_job(tmp_path)
    journal_path = tmp_path / "journal.json"

    source.unlink()

    result = ResumableImportExecutor().execute(
        operation_id="DF-SHUTTLE-REMOVED-001",
        queue=queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        delete_journal_when_complete=False,
    )

    journal = load_import_journal(journal_path)
    entry = next(iter(journal.entries.values()))

    assert result.completed == 0
    assert result.failed == 1
    assert entry.status is JournalStatus.FAILED
    assert destination.exists() is False


def test_crash_after_atomic_move_is_reconciled_on_resume(
    tmp_path: Path,
):
    queue, source, destination = make_single_job(tmp_path)
    journal_path = tmp_path / "journal.json"

    completed_events = 0

    def crash_after_move(event):
        nonlocal completed_events

        if event.stage is ImportStage.COMPLETED:
            completed_events += 1
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        ResumableImportExecutor().execute(
            operation_id="DF-CRASH-001",
            queue=queue,
            temp_dir=tmp_path / "temp",
            journal_path=journal_path,
            progress=crash_after_move,
            delete_journal_when_complete=False,
        )

    # The atomic move completed before the simulated process death.
    assert destination.exists()

    resumed_queue = ImportQueue()
    resumed_queue.add(make_job(source, destination))

    events = []

    result = ResumableImportExecutor().execute(
        operation_id="DF-CRASH-001",
        queue=resumed_queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        progress=events.append,
        delete_journal_when_complete=False,
    )

    assert result.completed == 1
    assert result.failed == 0
    assert destination.read_bytes() == source.read_bytes()

    assert any(
        event.stage is ImportStage.RESUMED
        for event in events
    )


def test_corrupt_existing_destination_is_never_overwritten(
    tmp_path: Path,
):
    queue, source, destination = make_single_job(tmp_path)
    journal_path = tmp_path / "journal.json"

    destination.write_bytes(b"wrong library content")

    result = ResumableImportExecutor().execute(
        operation_id="DF-CORRUPT-001",
        queue=queue,
        temp_dir=tmp_path / "temp",
        journal_path=journal_path,
        delete_journal_when_complete=False,
    )

    assert result.completed == 0
    assert result.failed == 1

    # DeckFlix must preserve the conflicting file for inspection.
    assert destination.read_bytes() == b"wrong library content"
    assert source.read_bytes() == b"verified media data"
