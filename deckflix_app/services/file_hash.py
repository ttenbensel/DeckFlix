import hashlib
from pathlib import Path


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
