from deckflix_app.importer import sha256, verify


def test_checksum(tmp_path):
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"

    a.write_bytes(b"deckflix")
    b.write_bytes(b"deckflix")

    assert sha256(a) == sha256(b)
    assert verify(a, b)


def test_checksum_failure(tmp_path):
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"

    a.write_bytes(b"deckflix")
    b.write_bytes(b"different")

    assert not verify(a, b)
