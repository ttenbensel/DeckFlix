from pathlib import Path

import pytest

from deckflix_app.operation import (
    OperationManager,
    create_final_safety_certificate,
    execute_empty_and_unmount,
    validate_snapshot_evidence,
)


def build_manager(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"
    shuttle.mkdir()

    first = shuttle / "one.mkv"
    first.write_bytes(b"one")

    nested = (
        shuttle
        / "folder"
        / "two.mkv"
    )

    nested.parent.mkdir()
    nested.write_bytes(b"two")

    manager = OperationManager()

    manager.begin(
        shuttle,
        operation_id="DF-RELEASE-001",
    )

    library = tmp_path / "library"
    library.mkdir()

    from deckflix_app.operation.evidence import (
        file_sha256,
    )

    for source in (
        first,
        nested,
    ):
        relative = source.relative_to(
            shuttle
        )

        destination = (
            library
            / relative
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_bytes(
            source.read_bytes()
        )

        manager.require_ledger().mark_imported(
            relative,
            destination=destination,
            sha256=file_sha256(
                destination
            ),
        )

    validation = validate_snapshot_evidence(
        manager
    )

    assert validation.safe is True

    create_final_safety_certificate(
        manager,
        validation,
    )

    return manager, shuttle


def install_safe_release_mocks(
    monkeypatch,
    shuttle: Path,
):
    mounted = {
        "value": True,
    }

    def fake_is_mounted(path):
        return (
            mounted["value"]
            and Path(path).resolve()
            == shuttle.resolve()
        )

    def fake_command(args):
        if args[0] == "findmnt":
            return (
                f"{shuttle.resolve()} "
                "/dev/test1 exfat"
            )

        if args[0] == "lsblk":
            return "SHUTTLE"

        if args[:2] == [
            "sudo",
            "umount",
        ]:
            mounted["value"] = False
            return ""

        raise AssertionError(
            f"Unexpected command: {args}"
        )

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "is_shuttle_mounted",
        fake_is_mounted,
    )

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "_run_command",
        fake_command,
    )

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "os.sync",
        lambda: None,
    )

    return mounted


def test_empty_and_unmount_deletes_only_shuttle_contents(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    install_safe_release_mocks(
        monkeypatch,
        shuttle,
    )

    result = execute_empty_and_unmount(
        manager,
        confirmation="DF-RELEASE-001",
    )

    assert result.emptied is True
    assert result.unmounted is True
    assert result.filesystem == "exfat"
    assert result.label == "SHUTTLE"

    assert list(
        shuttle.iterdir()
    ) == []

    # Evidence/library files remain intact.
    assert (
        tmp_path
        / "library"
        / "one.mkv"
    ).exists()

    assert (
        tmp_path
        / "library"
        / "folder"
        / "two.mkv"
    ).exists()


def test_wrong_confirmation_blocks_before_delete(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    install_safe_release_mocks(
        monkeypatch,
        shuttle,
    )

    with pytest.raises(
        RuntimeError,
        match="Confirmation token",
    ):
        execute_empty_and_unmount(
            manager,
            confirmation="WRONG",
        )

    assert (
        shuttle
        / "one.mkv"
    ).exists()


def test_wrong_filesystem_blocks_before_delete(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    mounted = {
        "value": True,
    }

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "is_shuttle_mounted",
        lambda path: mounted["value"],
    )

    def fake_command(args):
        if args[0] == "findmnt":
            return (
                f"{shuttle.resolve()} "
                "/dev/test1 ext4"
            )

        if args[0] == "lsblk":
            return "SHUTTLE"

        raise AssertionError(args)

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "_run_command",
        fake_command,
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected shuttle filesystem",
    ):
        execute_empty_and_unmount(
            manager,
            confirmation="DF-RELEASE-001",
        )

    assert (
        shuttle
        / "one.mkv"
    ).exists()


def test_wrong_label_blocks_before_delete(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "is_shuttle_mounted",
        lambda path: True,
    )

    def fake_command(args):
        if args[0] == "findmnt":
            return (
                f"{shuttle.resolve()} "
                "/dev/test1 exfat"
            )

        if args[0] == "lsblk":
            return "NOT-SHUTTLE"

        raise AssertionError(args)

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "_run_command",
        fake_command,
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected shuttle volume label",
    ):
        execute_empty_and_unmount(
            manager,
            confirmation="DF-RELEASE-001",
        )

    assert (
        shuttle
        / "one.mkv"
    ).exists()


def test_changed_evidence_blocks_before_delete(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    install_safe_release_mocks(
        monkeypatch,
        shuttle,
    )

    evidence = (
        tmp_path
        / "library"
        / "one.mkv"
    )

    # Same-size external corruption.
    evidence.write_bytes(
        b"xxx"
    )

    with pytest.raises(
        RuntimeError,
        match="preflight blocked",
    ):
        execute_empty_and_unmount(
            manager,
            confirmation="DF-RELEASE-001",
        )

    assert (
        shuttle
        / "one.mkv"
    ).exists()


def test_unmount_failure_does_not_hide_empty_state(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "is_shuttle_mounted",
        lambda path: True,
    )

    def fake_command(args):
        if args[0] == "findmnt":
            return (
                f"{shuttle.resolve()} "
                "/dev/test1 exfat"
            )

        if args[0] == "lsblk":
            return "SHUTTLE"

        if args[:2] == [
            "sudo",
            "umount",
        ]:
            raise RuntimeError(
                "simulated unmount failure"
            )

        raise AssertionError(args)

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "_run_command",
        fake_command,
    )

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "os.sync",
        lambda: None,
    )

    with pytest.raises(
        RuntimeError,
        match="unmount failure",
    ):
        execute_empty_and_unmount(
            manager,
            confirmation="DF-RELEASE-001",
        )

    # Deletion succeeded before the simulated unmount
    # failure, so the disk is empty but still mounted.
    assert list(
        shuttle.iterdir()
    ) == []


def test_unmount_only_preserves_shuttle_contents(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    install_safe_release_mocks(
        monkeypatch,
        shuttle,
    )

    from deckflix_app.operation import (
        execute_unmount_only,
    )

    result = execute_unmount_only(
        manager
    )

    assert result.emptied is False
    assert result.unmounted is True
    assert result.deleted_entries == 0

    assert (
        shuttle
        / "one.mkv"
    ).exists()

    assert (
        shuttle
        / "folder"
        / "two.mkv"
    ).exists()


def test_unmount_only_wrong_label_is_blocked(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "is_shuttle_mounted",
        lambda path: True,
    )

    def fake_command(args):
        if args[0] == "findmnt":
            return (
                f"{shuttle.resolve()} "
                "/dev/test1 exfat"
            )

        if args[0] == "lsblk":
            return "WRONG"

        raise AssertionError(args)

    monkeypatch.setattr(
        "deckflix_app.operation.shuttle_release."
        "_run_command",
        fake_command,
    )

    from deckflix_app.operation import (
        execute_unmount_only,
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected shuttle volume label",
    ):
        execute_unmount_only(
            manager
        )

    assert (
        shuttle
        / "one.mkv"
    ).exists()


def test_unmount_only_requires_current_snapshot(
    tmp_path: Path,
    monkeypatch,
):
    manager, shuttle = build_manager(
        tmp_path
    )

    install_safe_release_mocks(
        monkeypatch,
        shuttle,
    )

    (
        shuttle
        / "changed.mkv"
    ).write_bytes(
        b"changed"
    )

    from deckflix_app.operation import (
        execute_unmount_only,
    )

    with pytest.raises(Exception):
        execute_unmount_only(
            manager
        )

    assert (
        shuttle
        / "one.mkv"
    ).exists()
