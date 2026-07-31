import hashlib
from pathlib import Path


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def verify(source: Path, destination: Path) -> bool:
    return sha256(source) == sha256(destination)
