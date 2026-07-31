from deckflix_app.importer import atomic_move


def test_atomic_move(tmp_path):
    temp = tmp_path / "temp.mkv"
    temp.write_text("deckflix")

    destination = tmp_path / "library" / "movie.mkv"

    result = atomic_move(temp, destination)

    assert result.exists()
    assert result.read_text() == "deckflix"
    assert not temp.exists()
