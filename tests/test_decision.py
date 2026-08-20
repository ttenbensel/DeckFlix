from pathlib import Path
from deckflix_app.decision import Action
from deckflix_app.decision import decide
from deckflix_app.metadata.parser import parse_filename


def test_new_movie():
    incoming = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    result = decide(None, incoming)

    assert result.action == Action.NEW


def test_upgrade():
    existing = parse_filename(
        "Avatar (2009) 720p WEB-DL x264.mkv"
    )

    incoming = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    result = decide(existing, incoming)

    assert result.action == Action.UPGRADE


def test_duplicate():
    existing = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    incoming = parse_filename(
        "Avatar (2009) 1080p BluRay x265.mkv"
    )

    result = decide(existing, incoming)

    assert result.action == Action.DUPLICATE


def test_downgrade():
    existing = parse_filename(
        "Avatar (2009) 2160p Remux HEVC.mkv"
    )

    incoming = parse_filename(
        "Avatar (2009) 720p WEB-DL x264.mkv"
    )

    result = decide(existing, incoming)

    assert result.action == Action.DOWNGRADE


def test_verified_quality_can_correct_filename_decision():
    from deckflix_app.decision.engine import (
        decide_with_technical,
    )
    from deckflix_app.metadata.technical import (
        TechnicalMetadata,
        VideoStreamMetadata,
    )

    existing = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    incoming = parse_filename(
        "Avatar (2009) 720p BluRay HEVC.mkv"
    )

    filename_result = decide(
        existing,
        incoming,
    )

    assert (
        filename_result.action
        == Action.DOWNGRADE
    )

    incoming_technical = TechnicalMetadata(
        path=Path("/tmp/avatar-2160p.mkv"),
        probe_ok=True,
        primary_video=VideoStreamMetadata(
            index=0,
            width=3840,
            height=2160,
            codec="hevc",
        ),
    )

    verified_result = decide_with_technical(
        existing,
        incoming,
        incoming_technical=incoming_technical,
    )

    assert (
        verified_result.action
        == Action.UPGRADE
    )


def test_failed_technical_probe_preserves_filename_decision():
    from deckflix_app.decision.engine import (
        decide_with_technical,
    )
    from deckflix_app.metadata.technical import (
        TechnicalMetadata,
        VideoStreamMetadata,
    )

    existing = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    incoming = parse_filename(
        "Avatar (2009) 720p BluRay HEVC.mkv"
    )

    baseline = decide(
        existing,
        incoming,
    )

    failed_probe = TechnicalMetadata(
        path=Path("/tmp/avatar-failed.mkv"),
        probe_ok=False,
    )

    verified = decide_with_technical(
        existing,
        incoming,
        incoming_technical=failed_probe,
    )

    assert verified == baseline


def test_verified_quality_does_not_change_approval_policy():
    from deckflix_app.decision import (
        ApprovalStatus,
        default_approval_status,
    )
    from deckflix_app.decision.engine import (
        decide_with_technical,
    )
    from deckflix_app.metadata.technical import (
        TechnicalMetadata,
        VideoStreamMetadata,
    )

    existing = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    incoming = parse_filename(
        "Avatar (2009) 720p BluRay HEVC.mkv"
    )

    result = decide_with_technical(
        existing,
        incoming,
        incoming_technical=TechnicalMetadata(
            path=Path("/tmp/avatar-2160p.mkv"),
            probe_ok=True,
            primary_video=VideoStreamMetadata(
                index=0,
                width=3840,
                height=2160,
                codec="hevc",
            ),
        ),
    )

    assert result.action == Action.UPGRADE
    assert (
        default_approval_status(
            result.action
        )
        is ApprovalStatus.REVIEW
    )
