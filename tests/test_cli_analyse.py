from deckflix_app.cli.analyse import analyse


def test_cli_analyse(tmp_path, capsys):
    library = tmp_path / "library"
    shuttle = tmp_path / "shuttle"

    library.mkdir()
    shuttle.mkdir()

    (library / "Avatar (2009) 720p WEB-DL x264.mkv").touch()
    (shuttle / "Avatar (2009) 1080p BluRay HEVC.mkv").touch()
    (shuttle / "Alien (1979) 1080p BluRay HEVC.mkv").touch()

    analyse(str(library), str(shuttle))

    output = capsys.readouterr().out

    assert "DECKFLIX IMPORT REPORT" in output
    assert "Upgrades" in output
    assert "New" in output
