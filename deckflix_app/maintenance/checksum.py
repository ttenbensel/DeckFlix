from hashlib import sha256
from pathlib import Path


def file_checksum(
    path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """
    Calculate SHA256 checksum for a file.
    """

    digest = sha256()

    with Path(path).open(
        "rb"
    ) as file:

        while True:
            chunk = file.read(
                chunk_size
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()
