from pathlib import Path

from deckflix_app.decision import Action, Decision
from deckflix_app.importer import ImportJob, ImportQueue, execute


def test_execute(tmp_path):
    source = tmp_path / "movie.mkv"
    source.write_text("deckflix")

    destination = tmp_path / "library" / "movie.mkv"

    queue = ImportQueue()

    queue.add(
        ImportJob(
            source=source,
            destination=destination,
            decision=Decision(
                action=Action.NEW,
                reason="",
                existing_score=0,
                incoming_score=100,
            ),
        )
    )

    failures = execute(queue, tmp_path / "temp")

    assert failures == []
    assert destination.exists()
    assert destination.read_text() == "deckflix"
