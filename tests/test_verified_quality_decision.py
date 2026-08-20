from pathlib import Path

from deckflix_app.decision import Action
from deckflix_app.decision.engine import (
    decide_with_technical,
)
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.technical import (
    TechnicalMetadata,
    VideoStreamMetadata,
)


def media(
    *,
    resolution="1080p",
    source=None,
    codec="H264",
):
    return MediaMetadata(
        media_type="movie",
        title="Avatar",
        year=2009,
        resolution=resolution,
        source=source,
        video_codec=codec,
        path=Path("/tmp/avatar.mkv"),
    )


def technical(
    *,
    width=1920,
    height=1080,
    codec="h264",
    probe_ok=True,
):
    video = VideoStreamMetadata(
        index=0,
        codec=codec,
        width=width,
        height=height,
    )

    return TechnicalMetadata(
        path=Path("/tmp/avatar.mkv"),
        probe_ok=probe_ok,
        primary_video=video,
        video_streams=[video],
    )


def test_verified_equal_stream_ignores_release_source():
    existing = media(
        source="WEBRip",
    )

    incoming = media(
        source="Remux",
    )

    result = decide_with_technical(
        existing,
        incoming,
        existing_technical=technical(),
        incoming_technical=technical(),
    )

    assert result.action is Action.DUPLICATE
    assert (
        result.reason
        == "Verified technical quality is equivalent"
    )


def test_verified_resolution_beats_release_source():
    existing = media(
        resolution="2160p",
        source="WEBRip",
    )

    incoming = media(
        resolution="1080p",
        source="Remux",
    )

    result = decide_with_technical(
        existing,
        incoming,
        existing_technical=technical(
            width=3840,
            height=2160,
        ),
        incoming_technical=technical(
            width=1920,
            height=1080,
        ),
    )

    assert result.action is Action.DOWNGRADE


def test_verified_incoming_resolution_upgrade():
    existing = media(
        resolution="1080p",
        source="Remux",
    )

    incoming = media(
        resolution="2160p",
        source="WEBRip",
    )

    result = decide_with_technical(
        existing,
        incoming,
        existing_technical=technical(
            width=1920,
            height=1080,
        ),
        incoming_technical=technical(
            width=3840,
            height=2160,
        ),
    )

    assert result.action is Action.UPGRADE


def test_verified_codec_breaks_equal_resolution_tie():
    existing = media(
        source="Remux",
        codec="H264",
    )

    incoming = media(
        source="WEBRip",
        codec="HEVC",
    )

    result = decide_with_technical(
        existing,
        incoming,
        existing_technical=technical(
            codec="h264",
        ),
        incoming_technical=technical(
            codec="hevc",
        ),
    )

    assert result.action is Action.UPGRADE


def test_verified_existing_codec_can_win():
    existing = media(
        source="WEBRip",
        codec="HEVC",
    )

    incoming = media(
        source="Remux",
        codec="H264",
    )

    result = decide_with_technical(
        existing,
        incoming,
        existing_technical=technical(
            codec="hevc",
        ),
        incoming_technical=technical(
            codec="h264",
        ),
    )

    assert result.action is Action.DOWNGRADE


def test_failed_probe_preserves_filename_fallback():
    existing = media(
        source="WEBRip",
    )

    incoming = media(
        source="Remux",
    )

    result = decide_with_technical(
        existing,
        incoming,
        existing_technical=technical(
            probe_ok=False,
        ),
        incoming_technical=technical(),
    )

    assert result.action is Action.UPGRADE
    assert (
        result.reason
        == "Incoming file is higher quality"
    )


def test_missing_probe_preserves_filename_fallback():
    existing = media(
        source="WEBRip",
    )

    incoming = media(
        source="Remux",
    )

    result = decide_with_technical(
        existing,
        incoming,
        existing_technical=None,
        incoming_technical=technical(),
    )

    assert result.action is Action.UPGRADE


def test_new_media_does_not_require_verified_comparison():
    incoming = media(
        source="WEBRip",
    )

    result = decide_with_technical(
        None,
        incoming,
        existing_technical=None,
        incoming_technical=None,
    )

    assert result.action is Action.NEW
