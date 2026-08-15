from pathlib import Path

import pytest

from deckflix_app.operation.snapshot import (
    create_shuttle_snapshot,
)
from deckflix_app.shuttle_mount import (
    is_shuttle_mounted,
    require_shuttle_mounted,
)


pytestmark = pytest.mark.real_shuttle_mount


def test_existing_directory_is_not_a_connected_shuttle(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    assert shuttle.exists()

    assert (
        is_shuttle_mounted(shuttle)
        is False
    )


def test_require_shuttle_mounted_rejects_plain_directory(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    with pytest.raises(
        RuntimeError,
        match="Shuttle is not mounted",
    ):
        require_shuttle_mounted(
            shuttle
        )


def test_snapshot_refuses_unmounted_directory(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    media = (
        shuttle
        / "Movie"
        / "Movie.2026.mkv"
    )

    media.parent.mkdir()
    media.write_bytes(
        b"media"
    )

    with pytest.raises(
        RuntimeError,
        match="not mounted",
    ):
        create_shuttle_snapshot(
            shuttle
        )
