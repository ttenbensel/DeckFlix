from deckflix_app.metadata.parser import parse_filename
from deckflix_app.quality import compare_quality, quality_score


def test_quality_score():
    movie = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    assert quality_score(movie) == 352


def test_upgrade():
    existing = parse_filename(
        "Avatar (2009) 720p BluRay x264.mkv"
    )

    incoming = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    assert compare_quality(existing, incoming) == 1


def test_downgrade():
    existing = parse_filename(
        "Avatar (2009) 2160p Remux HEVC.mkv"
    )

    incoming = parse_filename(
        "Avatar (2009) 1080p WEB-DL x264.mkv"
    )

    assert compare_quality(existing, incoming) == -1


def test_equal():
    a = parse_filename(
        "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    b = parse_filename(
        "Avatar (2009) 1080p BluRay x265.mkv"
    )

    assert compare_quality(a, b) == 0
