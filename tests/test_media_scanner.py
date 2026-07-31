from deckflix_app.scanner import scan_media


def test_scan_media(tmp_path):
    (tmp_path / "Avatar (2009) 1080p BluRay HEVC.mkv").touch()
    (tmp_path / "Alien (1979) 720p WEB-DL x264.mp4").touch()

    media = scan_media(tmp_path)

    assert len(media) == 2

    titles = {m.title for m in media}

    assert "Avatar" in titles
    assert "Alien" in titles

    for m in media:
        assert m.path is not None
        assert m.size >= 0
