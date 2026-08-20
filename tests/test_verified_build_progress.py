from pathlib import Path

from deckflix_app.decision import queue as queue_module
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.technical import (
    TechnicalMetadata,
    VideoStreamMetadata,
)


def _media(
    path: Path,
    *,
    title: str = "Example",
) -> MediaMetadata:
    return MediaMetadata(
        media_type="movie",
        title=title,
        content_type="movie",
        year=2026,
        season=None,
        episode=None,
        resolution="1080p",
        source=None,
        video_codec="h264",
        container=path.suffix.lstrip("."),
        path=path,
        size=100,
    )


def _technical(
    path: Path,
) -> TechnicalMetadata:
    resolved = Path(path).resolve()

    return TechnicalMetadata(
        path=resolved,
        probe_ok=True,
        primary_video=VideoStreamMetadata(
            index=0,
            width=1920,
            height=1080,
            codec="h264",
        ),
    )


def test_verified_queue_reports_unique_probes(
    monkeypatch,
    tmp_path,
):
    incoming_path = tmp_path / "incoming.mkv"
    existing_path = tmp_path / "existing.mkv"

    incoming_path.touch()
    existing_path.touch()

    incoming = _media(incoming_path)
    existing = _media(existing_path)

    probes = []
    events = []

    def fake_probe(path):
        resolved = Path(path).resolve()
        probes.append(resolved)

        return _technical(resolved)

    monkeypatch.setattr(
        queue_module,
        "probe_media",
        fake_probe,
    )

    queue_module._build_verified_decision_queue(
        incoming=[incoming],
        library=[existing],
        progress=events.append,
    )

    assert len(probes) == 2

    assert [event.completed for event in events] == [
        1,
        2,
    ]

    assert events[0].current_file == (
        incoming_path.resolve()
    )

    assert events[1].current_file == (
        existing_path.resolve()
    )


def test_verified_queue_progress_respects_probe_cache(
    monkeypatch,
    tmp_path,
):
    incoming_path = tmp_path / "incoming.mkv"
    existing_path = tmp_path / "existing.mkv"

    incoming_path.touch()
    existing_path.touch()

    incoming = _media(incoming_path)
    existing = _media(existing_path)

    events = []

    monkeypatch.setattr(
        queue_module,
        "probe_media",
        lambda path: _technical(
            Path(path)
        ),
    )

    queue_module._build_verified_decision_queue(
        incoming=[
            incoming,
            incoming,
        ],
        library=[existing],
        progress=events.append,
    )

    paths = [
        event.current_file
        for event in events
    ]

    assert paths.count(
        incoming_path.resolve()
    ) == 1

    assert paths.count(
        existing_path.resolve()
    ) == 1


def test_verified_queue_without_progress_is_preserved(
    monkeypatch,
    tmp_path,
):
    incoming_path = tmp_path / "incoming.mkv"
    existing_path = tmp_path / "existing.mkv"

    incoming_path.touch()
    existing_path.touch()

    monkeypatch.setattr(
        queue_module,
        "probe_media",
        lambda path: _technical(
            Path(path)
        ),
    )

    result = (
        queue_module._build_verified_decision_queue(
            incoming=[
                _media(incoming_path)
            ],
            library=[
                _media(existing_path)
            ],
        )
    )

    assert result.total == 1
