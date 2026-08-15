from pathlib import Path

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        (
            "real_shuttle_mount: "
            "use the real shuttle mount detector "
            "instead of the normal test simulation"
        ),
    )


@pytest.fixture(autouse=True)
def simulate_mounted_test_shuttle(
    monkeypatch,
    request,
):
    """
    Ordinary tests use temporary directories as shuttles.

    Production code must require a real mounted filesystem,
    so tests simulate that mount boundary centrally rather
    than weakening production safety checks.
    """
    if request.node.get_closest_marker(
        "real_shuttle_mount"
    ):
        return

    def test_mount_present(path):
        path = Path(path)

        return (
            path.exists()
            and path.is_dir()
        )

    monkeypatch.setattr(
        "deckflix_app.operation.snapshot."
        "is_shuttle_mounted",
        test_mount_present,
    )

    monkeypatch.setattr(
        "deckflix_app.home_screen."
        "is_shuttle_mounted",
        test_mount_present,
    )

    monkeypatch.setattr(
        "deckflix_app.inventory.scanner."
        "is_shuttle_mounted",
        test_mount_present,
    )

    monkeypatch.setattr(
        "deckflix_app.shuttle."
        "is_shuttle_mounted",
        test_mount_present,
    )
