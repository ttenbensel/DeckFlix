from pathlib import Path

from deckflix_app.importer import (
    ImportProgress,
    ImportStage,
)
from deckflix_app.screens.import_monitor import (
    TerminalImportMonitor,
)


def test_progress_bar():
    assert (
        TerminalImportMonitor._progress_bar(
            50,
            width=10,
        )
        == "[#####-----]"
    )


def test_time_formatting():
    assert (
        TerminalImportMonitor._format_time(65)
        == "01:05"
    )
    assert (
        TerminalImportMonitor._format_time(3661)
        == "01:01:01"
    )


def test_monitor_tracks_completed_bytes(
    tmp_path: Path,
    capsys,
):
    source = tmp_path / "movie.mkv"
    source.write_bytes(b"12345")

    monitor = TerminalImportMonitor(
        operation_id="DF-MONITOR-001"
    )

    monitor(
        ImportProgress(
            stage=ImportStage.COMPLETED,
            current=1,
            total=2,
            source=source,
            destination=tmp_path / "library.mkv",
            message="Complete",
        )
    )

    assert monitor.completed_files == 1
    assert monitor.completed_bytes == 5
    assert monitor.journal_saved is True

    output = capsys.readouterr().out
    assert "COMPLETED" in output
