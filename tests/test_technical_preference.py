from deckflix_app.metadata.quality_verification import (
    QualityVerification,
    technical_preference,
)


def verified(
    resolution,
    codec,
):
    return QualityVerification(
        resolution=resolution,
        video_codec=codec,
        changed=True,
    )


def test_higher_resolution_is_preferred():
    result = technical_preference(
        [
            verified("1080p", "hevc"),
            verified("2160p", "h264"),
        ]
    )

    assert result is not None
    assert result.index == 1
    assert (
        result.reason
        == "higher verified resolution"
    )


def test_codec_breaks_equal_resolution_tie():
    result = technical_preference(
        [
            verified("1080p", "h264"),
            verified("1080p", "hevc"),
        ]
    )

    assert result is not None
    assert result.index == 1
    assert (
        result.reason
        == (
            "same verified resolution, "
            "preferred video codec"
        )
    )


def test_av1_can_break_equal_resolution_tie():
    result = technical_preference(
        [
            verified("1080p", "hevc"),
            verified("1080p", "av1"),
        ]
    )

    assert result is not None
    assert result.index == 1


def test_equal_verified_quality_has_no_preference():
    result = technical_preference(
        [
            verified("1080p", "h264"),
            verified("1080p", "h264"),
        ]
    )

    assert result is None


def test_failed_verification_does_not_create_preference():
    result = technical_preference(
        [
            verified("1080p", "h264"),
            None,
        ]
    )

    assert result is None


def test_unknown_resolution_does_not_create_preference():
    result = technical_preference(
        [
            verified(None, "hevc"),
            verified(None, "h264"),
        ]
    )

    assert result is None


def test_single_candidate_has_no_preference():
    result = technical_preference(
        [
            verified("2160p", "hevc"),
        ]
    )

    assert result is None
