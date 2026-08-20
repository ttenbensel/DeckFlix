from pathlib import Path

from deckflix_app.library.integrity import (
    MediaIntegrityStatus,
    classify_media_integrity,
)
from deckflix_app.metadata.models import (
    MediaMetadata,
)
from deckflix_app.metadata.technical import (
    TechnicalMetadata,
    VideoStreamMetadata,
)


def media(
    path: str,
    *,
    media_type: str = "movie",
    content_type: str = "movie",
    size: int = 100_000_000,
) -> MediaMetadata:
    return MediaMetadata(
        media_type=media_type,
        title="Test",
        content_type=content_type,
        year=2025 if media_type == "movie" else None,
        season=1 if content_type == "episode" else None,
        episode=1 if content_type == "episode" else None,
        resolution=None,
        source=None,
        video_codec=None,
        container=Path(path).suffix.lstrip("."),
        path=Path(path),
        size=size,
    )


def technical(
    path: str,
    *,
    probe_ok: bool = True,
    duration: float | None = 3600.0,
    error: str | None = None,
    video: bool = True,
) -> TechnicalMetadata:
    primary = (
        VideoStreamMetadata(
            index=0,
            codec="h264",
            width=1920,
            height=1080,
        )
        if video
        else None
    )

    return TechnicalMetadata(
        path=Path(path),
        probe_ok=probe_ok,
        error=error,
        duration_seconds=duration,
        size=100_000_000,
        primary_video=primary,
        video_streams=(
            [primary]
            if primary is not None
            else []
        ),
    )


def test_normal_movie_is_healthy():
    path = "/media/Alien.1979.mkv"

    result = classify_media_integrity(
        media(path),
        technical(
            path,
            duration=7000,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.HEALTHY
    )
    assert result.usable_as_primary_media is True
    assert result.requires_review is False


def test_normal_episode_is_healthy():
    path = (
        "/media/Barry/Season 01/"
        "Barry.S01E01.mkv"
    )

    result = classify_media_integrity(
        media(
            path,
            media_type="tv",
            content_type="episode",
        ),
        technical(
            path,
            duration=1800,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.HEALTHY
    )


def test_zero_byte_movie_is_corrupt():
    path = "/media/Avatar.2010.mp4"

    result = classify_media_integrity(
        media(
            path,
            size=0,
        ),
        technical(
            path,
            probe_ok=False,
            duration=None,
            error="moov atom not found",
            video=False,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.CORRUPT
    )
    assert result.usable_as_primary_media is False
    assert result.requires_review is True
    assert "zero bytes" in result.reasons[0]


def test_unprobeable_nonempty_movie_is_corrupt():
    path = "/media/Shazam.2023.mkv"

    result = classify_media_integrity(
        media(
            path,
            size=7_000_000_000,
        ),
        technical(
            path,
            probe_ok=False,
            duration=None,
            error="EBML header parsing failed",
            video=False,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.CORRUPT
    )
    assert any(
        "EBML" in reason
        for reason in result.reasons
    )


def test_episode_under_five_minutes_is_suspicious():
    path = (
        "/media/Blindspot/Season 04/"
        "Blindspot.S04E15.mkv"
    )

    result = classify_media_integrity(
        media(
            path,
            media_type="tv",
            content_type="episode",
        ),
        technical(
            path,
            duration=4.586,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.SUSPICIOUS
    )
    assert result.usable_as_primary_media is False
    assert result.requires_review is True


def test_episode_over_five_minutes_is_not_flagged():
    path = (
        "/media/Short Show/Season 01/"
        "Short.Show.S01E01.mkv"
    )

    result = classify_media_integrity(
        media(
            path,
            media_type="tv",
            content_type="episode",
        ),
        technical(
            path,
            duration=301,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.HEALTHY
    )


def test_ordinary_movie_under_ten_minutes_is_suspicious():
    path = "/media/Fake.Movie.2025.mkv"

    result = classify_media_integrity(
        media(path),
        technical(
            path,
            duration=300,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.SUSPICIOUS
    )


def test_sample_is_auxiliary_not_suspicious():
    path = (
        "/media/The Mummy/SAMPLE/"
        "sample.avi"
    )

    result = classify_media_integrity(
        media(path),
        technical(
            path,
            duration=9.1,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.AUXILIARY
    )
    assert result.usable_as_primary_media is False
    assert result.requires_review is False


def test_extra_is_auxiliary():
    path = (
        "/media/Breaking Bad/Extras/"
        "Deleted Scene.mkv"
    )

    result = classify_media_integrity(
        media(
            path,
            media_type="tv",
            content_type="extra",
        ),
        technical(
            path,
            duration=30,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.AUXILIARY
    )


def test_deleted_scene_path_is_auxiliary():
    path = (
        "/media/Show/Deleted Scenes/"
        "Alternate Ending.mkv"
    )

    result = classify_media_integrity(
        media(path),
        technical(
            path,
            duration=25,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.AUXILIARY
    )


def test_appledouble_is_auxiliary_even_if_probe_fails():
    path = (
        "/media/Pennyworth/Season 01/"
        "._Pennyworth.S01E01.mp4"
    )

    result = classify_media_integrity(
        media(
            path,
            media_type="tv",
            content_type="episode",
            size=4096,
        ),
        technical(
            path,
            probe_ok=False,
            duration=None,
            error="Invalid data found",
            video=False,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.AUXILIARY
    )
    assert "AppleDouble" in result.reasons[0]


def test_missing_duration_is_suspicious():
    path = "/media/Movie.2025.mkv"

    result = classify_media_integrity(
        media(path),
        technical(
            path,
            duration=None,
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.SUSPICIOUS
    )


def test_no_video_stream_is_corrupt():
    path = "/media/Movie.2025.mkv"

    result = classify_media_integrity(
        media(path),
        TechnicalMetadata(
            path=Path(path),
            probe_ok=True,
            duration_seconds=3600,
            size=100_000_000,
            primary_video=None,
            video_streams=[],
        ),
    )

    assert (
        result.status
        == MediaIntegrityStatus.CORRUPT
    )


def test_special_is_not_automatically_auxiliary():
    path = (
        "/media/South Park/Specials/"
        "South.Park.Special.mkv"
    )

    result = classify_media_integrity(
        media(
            path,
            media_type="tv",
            content_type="special",
        ),
        technical(
            path,
            duration=2900,
        ),
    )

    # "Specials" itself is intentionally not an
    # auxiliary directory marker. Full TV specials
    # remain normal playable programme content.
    assert (
        result.status
        == MediaIntegrityStatus.HEALTHY
    )
