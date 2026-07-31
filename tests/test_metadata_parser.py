from deckflix_app.metadata.parser import parse_filename


def test_parse_movie():
    media = parse_filename(
        "Avatar (2009) 1080p BluRay x264 DTS.mkv"
    )

    assert media.media_type == "movie"
    assert media.title == "Avatar"
    assert media.year == 2009
    assert media.resolution == "1080p"
    assert media.source.lower() == "bluray"
    assert media.video_codec.lower() == "x264"
    assert media.container == "mkv"


def test_parse_tv():
    media = parse_filename(
        "The.Last.of.Us.S01E04.2160p.WEB-DL.HEVC.mkv"
    )

    assert media.media_type == "tv"
    assert media.title == "The Last of Us"
    assert media.season == 1
    assert media.episode == 4
    assert media.resolution == "2160p"
    assert media.source.lower() == "web-dl"
    assert media.video_codec.lower() == "hevc"
    assert media.container == "mkv"
