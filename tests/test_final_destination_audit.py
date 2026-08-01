from pathlib import Path
from typing import cast

from deckflix_app.decision import Decision
from deckflix_app.importer import (
    ImportJob,
    ImportQueue,
    ImportResult,
    ShuttleSafetyChecker,
)


def build_completed_queue(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    library = tmp_path / "library"
    temp = tmp_path / "temp"

    shuttle.mkdir()
    library.mkdir()
    temp.mkdir()

    source = shuttle / "movie.mkv"
    destination = library / "movie.mkv"

    source.write_bytes(
        b"verified media"
    )
    destination.write_bytes(
        b"verified media"
    )

    job = ImportJob(
        source=source,
        destination=destination,
        decision=cast(
            Decision,
            object(),
        ),
    )

    job.copied = True
    job.verified = True
    job.completed = True

    queue = ImportQueue()
    queue.add(job)

    result = ImportResult(
        total=1,
        completed=1,
        failed=0,
    )

    return (
        queue,
        result,
        shuttle,
        temp,
        destination,
    )


def test_final_sha256_audit_passes(
    tmp_path: Path,
):
    (
        queue,
        result,
        shuttle,
        temp,
        _,
    ) = build_completed_queue(tmp_path)

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=result,
        shuttle_path=shuttle,
        temp_dir=temp,
    )

    assert safety.safe is True
    assert safety.audit_complete is True
    assert safety.audited_files == 1
    assert safety.total_files == 1
    assert safety.reasons == []


def test_corrupt_destination_blocks_certificate(
    tmp_path: Path,
):
    (
        queue,
        result,
        shuttle,
        temp,
        destination,
    ) = build_completed_queue(tmp_path)

    destination.write_bytes(
        b"corrupt media"
    )

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=result,
        shuttle_path=shuttle,
        temp_dir=temp,
    )

    assert safety.safe is False
    assert safety.audit_complete is False
    assert safety.audited_files == 0

    assert any(
        "SHA-256 audit" in reason
        for reason in safety.reasons
    )


def test_missing_destination_blocks_audit(
    tmp_path: Path,
):
    (
        queue,
        result,
        shuttle,
        temp,
        destination,
    ) = build_completed_queue(tmp_path)

    destination.unlink()

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=result,
        shuttle_path=shuttle,
        temp_dir=temp,
    )

    assert safety.safe is False
    assert safety.audit_complete is False

    assert any(
        "destination file(s) are missing"
        in reason
        for reason in safety.reasons
    )


def test_active_journal_is_not_treated_as_leftover_temp(
    tmp_path: Path,
):
    (
        queue,
        result,
        shuttle,
        temp,
        _,
    ) = build_completed_queue(tmp_path)

    journal = temp / "import-journal.json"
    journal.write_text(
        '{"operation": "DF-TEST"}',
        encoding="utf-8",
    )

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=result,
        shuttle_path=shuttle,
        temp_dir=temp,
        ignored_temp_paths={journal},
    )

    assert safety.safe is True
    assert safety.audit_complete is True


def test_unexpected_temp_file_still_blocks_completion(
    tmp_path: Path,
):
    (
        queue,
        result,
        shuttle,
        temp,
        _,
    ) = build_completed_queue(tmp_path)

    journal = temp / "import-journal.json"
    journal.write_text(
        '{"operation": "DF-TEST"}',
        encoding="utf-8",
    )

    leftover = temp / "partial-copy.mkv"
    leftover.write_bytes(b"incomplete")

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=result,
        shuttle_path=shuttle,
        temp_dir=temp,
        ignored_temp_paths={journal},
    )

    assert safety.safe is False
    assert any(
        "temporary import file" in reason
        for reason in safety.reasons
    )
