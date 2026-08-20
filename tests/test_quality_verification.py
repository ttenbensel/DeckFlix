from pathlib import Path

import deckflix_app.metadata.quality_verification as verification

from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.technical import (
    TechnicalMetadata,
    VideoStreamMetadata,
)


def make_media() -> MediaMetadata:
    return MediaMetadata(
        media_type="movie",
        title="Example",
        content_type="movie",
        year=2020,
        resolution="1080p",
        source="WEB-DL",
        video_codec="HEVC",
        path=Path("/media/example.mkv"),
        size=1000,
    )


def test_verification_reports_technical_change(
    monkeypatch,
):
    media = make_media()

    technical = TechnicalMetadata(
        path=media.path,
        probe_ok=True,
        primary_video=VideoStreamMetadata(
            index=0,
            codec="h264",
            width=1920,
            height=1080,
        ),
    )

    monkeypatch.setattr(
        verification,
        "probe_media",
        lambda path: technical,
    )

    result = verification.verify_quality(
        media
    )

    assert result is not None
    assert result.resolution == "1080p"
    assert result.video_codec == "h264"
    assert result.changed is True

    assert media.resolution == "1080p"
    assert media.video_codec == "HEVC"


def test_verification_unchanged_when_values_agree(
    monkeypatch,
):
    media = make_media()
    media.video_codec = "h264"

    technical = TechnicalMetadata(
        path=media.path,
        probe_ok=True,
        primary_video=VideoStreamMetadata(
            index=0,
            codec="h264",
            width=1920,
            height=1080,
        ),
    )

    monkeypatch.setattr(
        verification,
        "probe_media",
        lambda path: technical,
    )

    result = verification.verify_quality(
        media
    )

    assert result is not None
    assert result.changed is False


def test_failed_probe_returns_none(
    monkeypatch,
):
    media = make_media()

    technical = TechnicalMetadata(
        path=media.path,
        probe_ok=False,
        error="test failure",
    )

    monkeypatch.setattr(
        verification,
        "probe_media",
        lambda path: technical,
    )

    assert (
        verification.verify_quality(media)
        is None
    )


def test_missing_path_returns_none():
    media = make_media()
    media.path = None

    assert (
        verification.verify_quality(media)
        is None
    )
