import hashlib
from pathlib import Path

from deckflix_app.services.fingerprint_store import FingerprintStore


def sha256_file(path, chunk_size=8 * 1024 * 1024):
    """
    Calculate a SHA-256 hash without loading the whole file into memory.
    """

    path = Path(path)
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def cached_sha256_file(path, store=None):
    """
    Return a cached SHA-256 hash when the file is unchanged.

    Otherwise calculate it and save it to the fingerprint database.
    """

    path = Path(path)
    store = store or FingerprintStore()

    cached = store.get(path)

    if cached:
        return cached, True

    digest = sha256_file(path)
    store.save(path, digest)

    return digest, False
