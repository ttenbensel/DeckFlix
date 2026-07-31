from pathlib import Path

from deckflix_app.decision import Action, Decision
from deckflix_app.importer import ImportJob, copy_job


def test_copy_job(tmp_path):
    source = tmp_path / "movie.mkv"
    source.write_text("deckflix")

    destination = Path("/library/movie.mkv")

    job = ImportJob(
        source=source,
        destination=destination,
        decision=Decision(
            action=Action.NEW,
            reason="",
            existing_score=0,
            incoming_score=100,
        ),
    )

    temp = copy_job(job, tmp_path / "temp")

    assert temp.exists()
    assert temp.read_text() == "deckflix"
    assert job.copied
