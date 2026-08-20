from pathlib import Path
from types import SimpleNamespace

from deckflix_app.operation import OperationManager
from deckflix_app.system_verification import (
    run_system_verification,
)


def make_config(
    tmp_path: Path,
    *,
    read_only: bool = True,
    operating_profile: str = "ship_offline",
    low_impact: bool = True,
):
    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"
    reports = tmp_path / "reports"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    return SimpleNamespace(
        shuttle=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
        report_directory=reports,
        read_only=read_only,
        operating_profile=operating_profile,
        low_impact=low_impact,
    )


def test_system_verification_passes(
    tmp_path: Path,
):
    config = make_config(
        tmp_path
    )

    result = run_system_verification(
        config=config,
        operation_manager=OperationManager(),
        temp_directory=tmp_path / "temp",
    )

    assert result.ready is True
    assert result.failed == 0
    assert result.passed == len(
        result.checks
    )


def test_system_verification_reports_missing_shuttle(
    tmp_path: Path,
):
    config = make_config(
        tmp_path
    )

    Path(
        config.shuttle
    ).rmdir()

    result = run_system_verification(
        config=config,
        operation_manager=OperationManager(),
        temp_directory=tmp_path / "temp",
    )

    assert result.ready is False

    assert any(
        check.name == "Shuttle path"
        and check.passed is False
        for check in result.checks
    )


def test_system_verification_requires_safe_mode(
    tmp_path: Path,
):
    config = make_config(
        tmp_path,
        read_only=False,
    )

    result = run_system_verification(
        config=config,
        operation_manager=OperationManager(),
        temp_directory=tmp_path / "temp",
    )

    assert result.ready is False

    assert any(
        check.name == "Library Protection"
        and check.passed is False
        for check in result.checks
    )

def test_snapshot_verification_does_not_require_fake_mount(
    tmp_path: Path,
    monkeypatch,
):
    config = make_config(
        tmp_path
    )

    def refuse_mount_check(path):
        raise AssertionError(
            "Snapshot engine self-test must not "
            "invoke shuttle mount policy"
        )

    monkeypatch.setattr(
        "deckflix_app.operation.snapshot."
        "is_shuttle_mounted",
        refuse_mount_check,
    )

    result = run_system_verification(
        config=config,
        operation_manager=OperationManager(),
        temp_directory=tmp_path / "temp",
    )

    snapshot_check = next(
        check
        for check in result.checks
        if check.name == "Snapshot engine"
    )

    assert snapshot_check.passed is True
    assert "1 file" in snapshot_check.detail
    assert "fingerprint" in snapshot_check.detail

