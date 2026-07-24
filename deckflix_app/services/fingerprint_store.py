import sqlite3
from pathlib import Path


DEFAULT_DB = Path("/var/lib/deckflix/fingerprints.db")


class FingerprintStore:
    """
    Persistent cache for file fingerprints.

    A cached hash remains valid while the path, file size,
    and modification time remain unchanged.
    """

    def __init__(self, database_path=DEFAULT_DB):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialise(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS fingerprints (
                    path TEXT PRIMARY KEY,
                    size INTEGER NOT NULL,
                    modified_ns INTEGER NOT NULL,
                    sha256 TEXT NOT NULL
                )
                """
            )

    def get(self, path):
        path = Path(path)

        try:
            stat = path.stat()
        except OSError:
            return None

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT sha256
                FROM fingerprints
                WHERE path = ?
                  AND size = ?
                  AND modified_ns = ?
                """,
                (
                    str(path),
                    stat.st_size,
                    stat.st_mtime_ns,
                ),
            ).fetchone()

        return row[0] if row else None

    def save(self, path, sha256):
        path = Path(path)
        stat = path.stat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO fingerprints (
                    path,
                    size,
                    modified_ns,
                    sha256
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    size = excluded.size,
                    modified_ns = excluded.modified_ns,
                    sha256 = excluded.sha256
                """,
                (
                    str(path),
                    stat.st_size,
                    stat.st_mtime_ns,
                    sha256,
                ),
            )

    def count(self):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM fingerprints"
            ).fetchone()

        return row[0]
