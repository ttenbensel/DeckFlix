from pathlib import Path

from deckflix_app.metadata.enrichment import (
    enrich_quality_from_technical,
)
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.technical import (
    TechnicalMetadata,
    VideoStreamMetadata,
)
from deckflix_app.quality import quality_score


def make_media(
    *,
    resolution="720p",
    source="WEB-DL",
    video_codec="x264",
):
    return MediaMetadata(
        media_type="movie",
        title="Test Movie",
        content_type="movie",
        year=2026,
        resolution=resolution,
        source=source,
        video_codec=video_codec,
        container="mkv",
        path=Path("/media/Test Movie.mkv"),
        size=1000,
    )


def make_technical(
    *,
    probe_ok=True,
    width=1920,
    height=1080,
    codec="hevc",
):
    primary = None

    if width is not None and height is not None:
        primary = VideoStreamMetadata(
            index=0,
            codec=codec,
            width=width,
            height=height,
        )

    return TechnicalMetadata(
        path=Path("/media/Test Movie.mkv"),
        probe_ok=probe_ok,
        primary_video=primary,
        video_streams=(
            [primary]
            if primary is not None
            else []
        ),
    )


def test_probe_quality_overrides_filename_quality():
    media = make_media(
        resolution="720p",
        video_codec="x264",
    )

    technical = make_technical(
        width=1920,
        height=1080,
        codec="hevc",
    )

    enriched = enrich_quality_from_technical(
        media,
        technical,
    )

    assert enriched.resolution == "1080p"
    assert enriched.video_codec == "hevc"


def test_release_source_is_preserved():
    media = make_media(
        source="BluRay",
    )

    technical = make_technical()

    enriched = enrich_quality_from_technical(
        media,
        technical,
    )

    assert enriched.source == "BluRay"


def test_failed_probe_preserves_original_metadata():
    media = make_media(
        resolution="720p",
        video_codec="x264",
    )

    technical = TechnicalMetadata(
        path=Path("/media/Test Movie.mkv"),
        probe_ok=False,
        error="probe failed",
    )

    enriched = enrich_quality_from_technical(
        media,
        technical,
    )

    assert enriched is media
    assert enriched.resolution == "720p"
    assert enriched.video_codec == "x264"


def test_missing_probe_values_preserve_filename_values():
    media = make_media(
        resolution="720p",
        video_codec="x264",
    )

    technical = TechnicalMetadata(
        path=Path("/media/Test Movie.mkv"),
        probe_ok=True,
    )

    enriched = enrich_quality_from_technical(
        media,
        technical,
    )

    assert enriched is media
    assert enriched.resolution == "720p"
    assert enriched.video_codec == "x264"


def test_enrichment_changes_existing_quality_score():
    media = make_media(
        resolution="720p",
        source="WEB-DL",
        video_codec="x264",
    )

    technical = make_technical(
        width=1920,
        height=1080,
        codec="hevc",
    )

    enriched = enrich_quality_from_technical(
        media,
        technical,
    )

    assert quality_score(media) == 241
    assert quality_score(enriched) == 342
