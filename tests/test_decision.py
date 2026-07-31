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
