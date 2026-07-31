from pathlib import Path

from deckflix_app.decision import Action, Decision
from deckflix_app.importer import ImportJob, ImportQueue


def test_queue():
    queue = ImportQueue()

    job = ImportJob(
        source=Path("/tmp/a.mkv"),
        destination=Path("/library/a.mkv"),
        decision=Decision(
            action=Action.NEW,
            reason="",
            existing_score=0,
            incoming_score=100,
        ),
    )

    queue.add(job)

    assert len(queue.pending()) == 1

    job.completed = True

    assert len(queue.pending()) == 0
    assert len(queue.completed()) == 1
