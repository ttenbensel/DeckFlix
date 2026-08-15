from pathlib import Path

from deckflix_app.library import (
    LibraryAudit,
    LibraryAuditEntry,
    LibraryIssue,
    LibraryRepairAction,
    LibraryRepairStatus,
    LibraryRoot,
    build_library_repair_plan,
)
from deckflix_app.scanner import (
    metadata_from_file,
)


def make_entry(
    tmp_path: Path,
    *,
    filename: str,
    relative_path: Path | None = None,
    expected_type: str,
    issues=None,
):
    root = tmp_path / "source"

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    relative = (
        relative_path
        if relative_path is not None
        else Path(filename)
    )

    path = root / relative

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.touch()

    media = metadata_from_file(
        path
    )

    spec = LibraryRoot(
        name="Test Root",
        path=root,
        expected_media_type=expected_type,
        primary=False,
    )

    if issues is None:
        entry_issues = {
            LibraryIssue.MISPLACED,
        }
    else:
        entry_issues = set(
            issues
        )

    return LibraryAuditEntry(
        root=spec,
        media=media,
        relative_path=relative,
        issues=entry_issues,
    )


def plan_for(
    entry,
    tmp_path,
):
    audit = LibraryAudit(
        entries=[entry],
        duplicate_groups={},
    )

    return build_library_repair_plan(
        audit,
        movies_root=(
            tmp_path / "movies"
        ),
        tv_root=(
            tmp_path / "tv"
        ),
    )


def test_movie_gets_primary_movie_destination(
    tmp_path: Path,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Doctor.Sleep.2019.1080p.mkv"
        ),
        expected_type="tv",
    )

    plan = plan_for(
        entry,
        tmp_path,
    )

    item = plan.items[0]

    assert (
        item.status
        is LibraryRepairStatus.READY
    )

    assert (
        item.action
        is LibraryRepairAction.MOVE_RENAME
    )

    assert item.destination == (
        tmp_path
        / "movies"
        / "Doctor Sleep (2019)"
        / "Doctor Sleep (2019).mkv"
    )


def test_tv_episode_gets_season_destination(
    tmp_path: Path,
):
    root = (
        tmp_path
        / "source"
    )

    folder = (
        root
        / "Band of Brothers"
    )

    folder.mkdir(
        parents=True
    )

    for number in range(
        1,
        4,
    ):
        (
            folder
            / (
                "Band of Brothers "
                f"- Part {number:02d}.avi"
            )
        ).touch()

    target = (
        folder
        / "Band of Brothers - Part 01.avi"
    )

    media = metadata_from_file(
        target
    )

    spec = LibraryRoot(
        name="Test Root",
        path=root,
        expected_media_type="movie",
        primary=False,
    )

    entry = LibraryAuditEntry(
        root=spec,
        media=media,
        relative_path=(
            target.relative_to(
                root
            )
        ),
        issues={
            LibraryIssue.MISPLACED,
        },
    )

    plan = plan_for(
        entry,
        tmp_path,
    )

    item = plan.items[0]

    assert (
        item.status
        is LibraryRepairStatus.READY
    )

    assert (
        item.action
        is LibraryRepairAction.MOVE_RENAME
    )

    assert item.destination == (
        tmp_path
        / "tv"
        / "Band of Brothers"
        / "Season 01"
        / "Band of Brothers S01E01.avi"
    )


def test_episode_zero_requires_review(
    tmp_path: Path,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Adventure.Time.S01E00.mkv"
        ),
        expected_type="movie",
    )

    plan = plan_for(
        entry,
        tmp_path,
    )

    item = plan.items[0]

    assert (
        item.status
        is LibraryRepairStatus.REVIEW
    )

    assert (
        item.action
        is LibraryRepairAction.REVIEW
    )

    assert (
        "episode zero"
        in item.reason.lower()
    )


def test_existing_destination_blocks(
    tmp_path: Path,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Doctor.Sleep.2019.mkv"
        ),
        expected_type="tv",
    )

    destination = (
        tmp_path
        / "movies"
        / "Doctor Sleep (2019)"
        / "Doctor Sleep (2019).mkv"
    )

    destination.parent.mkdir(
        parents=True
    )

    destination.touch()

    plan = plan_for(
        entry,
        tmp_path,
    )

    item = plan.items[0]

    assert (
        item.status
        is LibraryRepairStatus.BLOCKED
    )

    assert (
        "already exists"
        in item.reason.lower()
    )


def test_same_proposed_destination_blocks_both(
    tmp_path: Path,
):
    first = make_entry(
        tmp_path / "a",
        filename=(
            "Alien.1979.1080p.mkv"
        ),
        expected_type="tv",
    )

    second = make_entry(
        tmp_path / "b",
        filename=(
            "Alien.1979.720p.mkv"
        ),
        expected_type="tv",
    )

    audit = LibraryAudit(
        entries=[
            first,
            second,
        ],
        duplicate_groups={},
    )

    plan = build_library_repair_plan(
        audit,
        movies_root=(
            tmp_path / "movies"
        ),
        tv_root=(
            tmp_path / "tv"
        ),
    )

    assert len(
        plan.items
    ) == 2

    assert all(
        item.status
        is LibraryRepairStatus.BLOCKED
        for item in plan.items
    )


def test_non_misplaced_is_not_planned(
    tmp_path: Path,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Alien.1979.mkv"
        ),
        expected_type="movie",
        issues=set(),
    )

    audit = LibraryAudit(
        entries=[entry],
        duplicate_groups={},
    )

    plan = build_library_repair_plan(
        audit,
        movies_root=(
            tmp_path / "movies"
        ),
        tv_root=(
            tmp_path / "tv"
        ),
    )

    assert plan.items == ()


def test_planner_does_not_change_source(
    tmp_path: Path,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Doctor.Sleep.2019.mkv"
        ),
        expected_type="tv",
    )

    source = entry.path

    plan_for(
        entry,
        tmp_path,
    )

    assert source.exists()


def test_planner_does_not_create_destination(
    tmp_path: Path,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Doctor.Sleep.2019.mkv"
        ),
        expected_type="tv",
    )

    expected = (
        tmp_path
        / "movies"
        / "Doctor Sleep (2019)"
        / "Doctor Sleep (2019).mkv"
    )

    plan_for(
        entry,
        tmp_path,
    )

    assert not expected.exists()
