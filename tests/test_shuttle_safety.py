from pathlib import Path
from typing import cast

from deckflix_app.decision import Decision
from deckflix_app.importer import (
    ImportJob,
    ImportQueue,
    ImportResult,
    ShuttleSafetyChecker,
)


def make_job(
    source: Path,
    destination: Path,
    *,
    copied: bool = True,
    verified: bool = True,
    completed: bool = True,
) -> ImportJob:
    return ImportJob(
        source=source,
        destination=destination,
        decision=cast(Decision, object()),
        copied=copied,
        verified=verified,
        completed=completed,
    )


def test_safe_when_all_import_checks_pass(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    temp_dir = tmp_path / "temporary"
    destination = tmp_path / "library" / "movie.mkv"
    source = shuttle / "movie.mkv"

    shuttle.mkdir()
    temp_dir.mkdir()
    destination.parent.mkdir()
    destination.write_bytes(b"verified media")

    queue = ImportQueue()
    queue.add(
        make_job(
            source=source,
            destination=destination,
        )
    )

    import_result = ImportResult(
        total=1,
        completed=1,
        failed=0,
    )

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=import_result,
        shuttle_path=shuttle,
        temp_dir=temp_dir,
    )

    assert safety.safe is True
    assert safety.status == "SAFE TO EMPTY"
    assert safety.reasons == []


def test_not_safe_when_import_failed(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    temp_dir = tmp_path / "temporary"
    destination = tmp_path / "library" / "movie.mkv"
    source = shuttle / "movie.mkv"

    shuttle.mkdir()
    temp_dir.mkdir()

    queue = ImportQueue()
    queue.add(
        make_job(
            source=source,
            destination=destination,
            copied=False,
            verified=False,
            completed=False,
        )
    )

    import_result = ImportResult(
        total=1,
        completed=0,
        failed=1,
    )

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=import_result,
        shuttle_path=shuttle,
        temp_dir=temp_dir,
    )

    assert safety.safe is False
    assert safety.status == "NOT SAFE TO EMPTY"
    assert any("failed" in reason for reason in safety.reasons)
    assert any("pending" in reason for reason in safety.reasons)


def test_not_safe_when_destination_is_missing(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    temp_dir = tmp_path / "temporary"
    destination = tmp_path / "library" / "missing.mkv"
    source = shuttle / "movie.mkv"

    shuttle.mkdir()
    temp_dir.mkdir()

    queue = ImportQueue()
    queue.add(
        make_job(
            source=source,
            destination=destination,
        )
    )

    import_result = ImportResult(
        total=1,
        completed=1,
        failed=0,
    )

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=import_result,
        shuttle_path=shuttle,
        temp_dir=temp_dir,
    )

    assert safety.safe is False
    assert any(
        "destination" in reason.lower()
        for reason in safety.reasons
    )


def test_not_safe_when_temp_files_remain(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    temp_dir = tmp_path / "temporary"
    destination = tmp_path / "library" / "movie.mkv"
    source = shuttle / "movie.mkv"

    shuttle.mkdir()
    temp_dir.mkdir()
    destination.parent.mkdir()
    destination.write_bytes(b"verified media")
    (temp_dir / "unfinished.part").write_bytes(b"partial")

    queue = ImportQueue()
    queue.add(
        make_job(
            source=source,
            destination=destination,
        )
    )

    import_result = ImportResult(
        total=1,
        completed=1,
        failed=0,
    )

    safety = ShuttleSafetyChecker().check(
        queue=queue,
        import_result=import_result,
        shuttle_path=shuttle,
        temp_dir=temp_dir,
    )

    assert safety.safe is False
    assert any(
        "temporary" in reason.lower()
        for reason in safety.reasons
    )


def test_empty_import_is_not_safe(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    temp_dir = tmp_path / "temporary"

    shuttle.mkdir()
    temp_dir.mkdir()

    safety = ShuttleSafetyChecker().check(
        queue=ImportQueue(),
        import_result=ImportResult(),
        shuttle_path=shuttle,
        temp_dir=temp_dir,
    )

    assert safety.safe is False
    assert any(
        "no import jobs" in reason.lower()
        for reason in safety.reasons
    )
