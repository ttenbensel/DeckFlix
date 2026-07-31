from deckflix_app.scanner import scan_directory


def test_scan_directory(tmp_path):
    (tmp_path / "Movies").mkdir()
    (tmp_path / "TV").mkdir()

    (tmp_path / "Movies" / "movie.mkv").touch()
    (tmp_path / "Movies" / "movie.mp4").touch()
    (tmp_path / "TV" / "show.mkv").touch()
    (tmp_path / "ignore.txt").touch()

    files = scan_directory(tmp_path)

    assert len(files) == 3

    assert any(f.name == "movie.mkv" for f in files)
    assert any(f.name == "movie.mp4" for f in files)
    assert any(f.name == "show.mkv" for f in files)
