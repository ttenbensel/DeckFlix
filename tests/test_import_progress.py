from pathlib import Path

from deckflix_app.decision import (
    Action,
    Decision,
)
from deckflix_app.importer import (
    ImportEngine,
    ImportJob,
    ImportProgress,
    ImportQueue,
    ImportStage,
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
            reason="Sandbox import",
            existing_score=0,
            incoming_score=100,
        ),
    )


def test_engine_emits_progress_events(
    tmp_path: Path,
):
    source = tmp_path / "source.mkv"
    destination = (
        tmp_path
        / "library"
        / "source.mkv"
    )

    source.write_bytes(b"media")

    queue = ImportQueue()
    queue.add(
        make_job(
            source,
            destination,
        )
    )

    events: list[ImportProgress] = []

    result = ImportEngine().execute(
        queue,
        tmp_path / "temp",
        progress=events.append,
    )

    stages = [
        event.stage
        for event in events
    ]

    assert result.completed == 1
    assert stages == [
        ImportStage.STARTING,
        ImportStage.COPYING,
        ImportStage.VERIFYING,
        ImportStage.MOVING,
        ImportStage.COMPLETED,
        ImportStage.FINISHED,
    ]

    assert events[-1].percent == 100
    assert destination.exists()


def test_progress_percent_handles_empty_queue(
    tmp_path: Path,
):
    events = []

    result = ImportEngine().execute(
        ImportQueue(),
        tmp_path / "temp",
        progress=events.append,
    )

    assert result.total == 0
    assert events[0].percent == 0
    assert events[-1].stage is ImportStage.FINISHED
