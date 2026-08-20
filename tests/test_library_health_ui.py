from pathlib import Path

import deckflix_app.library_health as ui

from deckflix_app.library import (
    DuplicateClassification,
    LibraryAudit,
    LibraryAuditEntry,
    LibraryIssue,
    LibraryRepairAction,
    LibraryRepairItem,
    LibraryRepairPlan,
    LibraryRepairStatus,
    LibraryRoot,
)
from deckflix_app.metadata.parser import (
    parse_filename,
)


def make_entry(
    tmp_path: Path,
    *,
    filename: str,
    root_name: str = "Primary Movies",
    expected_type: str = "movie",
    primary: bool = True,
    issues=None,
):
    root_path = (
        tmp_path
        / root_name.replace(" ", "_")
    )

    root_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        root_path
        / filename
    )

    path.touch()

    media = parse_filename(
        filename
    )

    media.path = path
    media.size = 0

    root = LibraryRoot(
        name=root_name,
        path=root_path,
        expected_media_type=expected_type,
        primary=primary,
    )

    return LibraryAuditEntry(
        root=root,
        media=media,
        relative_path=Path(
            filename
        ),
        issues=set(
            issues or []
        ),
    )


def make_repair_item(
    tmp_path: Path,
    *,
    status: LibraryRepairStatus,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Avatar (2009) 1080p.mkv"
        ),
        issues={
            LibraryIssue.MISPLACED,
        },
    )

    destination = (
        tmp_path
        / "destination"
        / "Avatar (2009)"
        / "Avatar (2009).mkv"
    )

    return LibraryRepairItem(
        entry=entry,
        source=entry.path,
        destination=destination,
        action=(
            LibraryRepairAction.MOVE_RENAME
            if status
            is LibraryRepairStatus.READY
            else LibraryRepairAction.REVIEW
        ),
        status=status,
        reason="Test repair reason.",
    )


def test_summary_shows_audit_counts(
    tmp_path: Path,
    capsys,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Avatar (2009) 1080p.mkv"
        ),
        issues={
            LibraryIssue.MISPLACED,
        },
    )

    audit = LibraryAudit(
        entries=[entry],
        duplicate_groups={},
    )

    ui._show_summary(
        audit
    )

    output = (
        capsys.readouterr().out
    )

    assert "Library Health" in output
    assert "Total videos          1" in output
    assert "Misplaced             1" in output
    assert "Read-only audit." in output
    assert (
        "No files have been changed."
        in output
    )


def test_issue_review_lists_path(
    tmp_path: Path,
    capsys,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Avatar (2009) 1080p.mkv"
        ),
        issues={
            LibraryIssue.MISPLACED,
        },
    )

    audit = LibraryAudit(
        entries=[entry],
        duplicate_groups={},
    )

    ui._show_issue_entries(
        audit,
        LibraryIssue.MISPLACED,
    )

    output = (
        capsys.readouterr().out
    )

    assert "Misplaced Media" in output
    assert "Avatar" in output
    assert (
        "Avatar (2009) 1080p.mkv"
        in output
    )


def test_duplicate_review_empty_is_read_only(
    capsys,
):
    audit = LibraryAudit(
        entries=[],
        duplicate_groups={},
    )

    ui._show_duplicate_groups(
        audit
    )

    output = (
        capsys.readouterr().out
    )

    assert "Duplicate Candidates" in output
    assert "None found." in output
    assert "No files have been changed." in output


def test_duplicate_review_shows_all_classifications(
    tmp_path: Path,
    capsys,
):
    entries = []
    groups = {}
    classifications = {}

    values = list(
        DuplicateClassification
    )

    for index, classification in enumerate(
        values,
        start=1,
    ):
        entry = make_entry(
            tmp_path / str(index),
            filename=(
                f"Movie {index} (2020) 1080p.mkv"
            ),
            issues={
                LibraryIssue.DUPLICATE_CANDIDATE,
            },
        )

        key = (
            "movie",
            f"movie-{index}",
            2020,
        )

        entries.append(entry)
        groups[key] = (entry,)
        classifications[key] = classification

    audit = LibraryAudit(
        entries=entries,
        duplicate_groups=groups,
        duplicate_classifications=classifications,
    )

    ui._show_duplicate_groups(
        audit
    )

    output = (
        capsys.readouterr().out
    )

    for classification in values:
        assert (
            classification.value
            in output
        )
        assert (
            ui.DUPLICATE_CLASSIFICATION_LABELS[
                classification
            ]
            in output
        )
        assert (
            ui.DUPLICATE_CLASSIFICATION_REASONS[
                classification
            ]
            in output
        )


def test_duplicate_review_shows_group(
    tmp_path: Path,
    capsys,
):
    first = make_entry(
        tmp_path,
        filename=(
            "Alien (1979) 1080p.mkv"
        ),
        root_name="Primary Movies",
        issues={
            LibraryIssue.DUPLICATE_CANDIDATE,
        },
    )

    second = make_entry(
        tmp_path,
        filename=(
            "Alien (1979) 720p.mkv"
        ),
        root_name="Legacy Movies",
        primary=False,
        issues={
            LibraryIssue.DUPLICATE_CANDIDATE,
            LibraryIssue.LEGACY_LOCATION,
        },
    )

    key = (
        "movie",
        "alien",
        1979,
    )

    audit = LibraryAudit(
        entries=[
            first,
            second,
        ],
        duplicate_groups={
            key: (
                first,
                second,
            )
        },
        duplicate_classifications={
            key:
                DuplicateClassification.LEGACY_DUPLICATE,
        },
    )

    ui._show_duplicate_groups(
        audit
    )

    output = (
        capsys.readouterr().out
    )

    assert "Duplicate Candidates" in output
    assert "Classification Summary" in output
    assert "Legacy duplicate" in output
    assert "LEGACY_DUPLICATE" in output
    assert "Alien (1979)" in output
    assert "Primary Movies" in output
    assert "Legacy Movies" in output
    assert "Reason:" in output
    assert "Groups: 1" in output
    assert "Candidate files: 2" in output
    assert "READ-ONLY" in output
    assert "No files have been changed." in output


def test_repair_plan_summary_shows_counts(
    tmp_path: Path,
    capsys,
):
    plan = LibraryRepairPlan(
        items=(
            make_repair_item(
                tmp_path / "ready",
                status=LibraryRepairStatus.READY,
            ),
            make_repair_item(
                tmp_path / "review",
                status=LibraryRepairStatus.REVIEW,
            ),
            make_repair_item(
                tmp_path / "blocked",
                status=LibraryRepairStatus.BLOCKED,
            ),
        )
    )

    ui._show_repair_plan_summary(
        plan
    )

    output = (
        capsys.readouterr().out
    )

    assert "Library Repair Plan" in output
    assert "Planned       3" in output
    assert "Ready         1" in output
    assert "Review        1" in output
    assert "Blocked       1" in output
    assert "READ-ONLY" in output
    assert (
        "No files will be changed."
        in output
    )


def test_repair_items_show_paths(
    tmp_path: Path,
    capsys,
):
    item = make_repair_item(
        tmp_path,
        status=LibraryRepairStatus.READY,
    )

    plan = LibraryRepairPlan(
        items=(
            item,
        )
    )

    ui._show_repair_items(
        plan,
        LibraryRepairStatus.READY,
    )

    output = (
        capsys.readouterr().out
    )

    assert "READY Repairs" in output
    assert "MOVE_RENAME" in output
    assert str(
        item.source
    ) in output
    assert str(
        item.destination
    ) in output
    assert "Test repair reason." in output
    assert "READ-ONLY" in output


def test_repair_plan_back_returns(
    monkeypatch,
):
    audit = LibraryAudit(
        entries=[],
        duplicate_groups={},
    )

    plan = LibraryRepairPlan(
        items=()
    )

    monkeypatch.setattr(
        ui,
        "build_library_repair_plan",
        lambda audit, **kwargs: plan,
    )

    answers = iter(
        ["5"]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(
            answers
        ),
    )

    assert (
        ui._show_repair_plan(
            audit
        )
        is None
    )


def test_library_health_opens_repair_plan(
    monkeypatch,
):
    audit = LibraryAudit(
        entries=[],
        duplicate_groups={},
    )

    called = []

    monkeypatch.setattr(
        ui,
        "audit_libraries",
        lambda roots: audit,
    )

    monkeypatch.setattr(
        ui,
        "current_deckflix_library_roots",
        lambda: [],
    )

    monkeypatch.setattr(
        ui,
        "_show_repair_plan",
        lambda audit: called.append(
            audit
        ),
    )

    answers = iter(
        [
            "7",
            "8",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(
            answers
        ),
    )

    ui.show_library_health()

    assert called == [
        audit
    ]


def test_back_returns_without_changes(
    monkeypatch,
):
    audit = LibraryAudit(
        entries=[],
        duplicate_groups={},
    )

    monkeypatch.setattr(
        ui,
        "audit_libraries",
        lambda roots: audit,
    )

    monkeypatch.setattr(
        ui,
        "current_deckflix_library_roots",
        lambda: [],
    )

    answers = iter(
        ["8"]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(
            answers
        ),
    )

    assert (
        ui.show_library_health()
        is None
    )


def test_duplicate_review_shows_verified_quality_change(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Alien (1979) 1080p HEVC.mkv"
        ),
        issues={
            LibraryIssue.DUPLICATE_CANDIDATE,
        },
    )

    key = (
        "movie",
        "alien",
        1979,
    )

    audit = LibraryAudit(
        entries=[entry],
        duplicate_groups={
            key: (entry,)
        },
        duplicate_classifications={
            key:
                DuplicateClassification.QUALITY_VARIANT,
        },
    )

    class Verification:
        resolution = "1080p"
        video_codec = "h264"
        changed = True

    monkeypatch.setattr(
        ui,
        "verify_quality",
        lambda media: Verification(),
    )

    ui._show_duplicate_groups(
        audit
    )

    output = capsys.readouterr().out

    assert (
        "Verified:     1080p / h264"
        in output
    )


def test_duplicate_review_hides_matching_verification(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    entry = make_entry(
        tmp_path,
        filename=(
            "Alien (1979) 1080p x264.mkv"
        ),
        issues={
            LibraryIssue.DUPLICATE_CANDIDATE,
        },
    )

    key = (
        "movie",
        "alien",
        1979,
    )

    audit = LibraryAudit(
        entries=[entry],
        duplicate_groups={
            key: (entry,)
        },
        duplicate_classifications={
            key:
                DuplicateClassification.QUALITY_VARIANT,
        },
    )

    class Verification:
        resolution = "1080p"
        video_codec = "h264"
        changed = False

    monkeypatch.setattr(
        ui,
        "verify_quality",
        lambda media: Verification(),
    )

    ui._show_duplicate_groups(
        audit
    )

    output = capsys.readouterr().out

    assert "Verified:" not in output


def test_duplicate_display_recommends_keep_and_remove(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    first = make_entry(
        tmp_path / "first",
        filename=(
            "Movie (2020) 480p.mkv"
        ),
        issues={
            LibraryIssue.DUPLICATE_CANDIDATE,
        },
    )

    second = make_entry(
        tmp_path / "second",
        filename=(
            "Movie (2020) 1080p.mkv"
        ),
        issues={
            LibraryIssue.DUPLICATE_CANDIDATE,
        },
    )

    key = (
        "movie",
        "movie",
        2020,
        None,
    )

    audit = LibraryAudit(
        entries=[
            first,
            second,
        ],
        duplicate_groups={
            key: (
                first,
                second,
            ),
        },
        duplicate_classifications={
            key: (
                DuplicateClassification
                .QUALITY_VARIANT
            ),
        },
    )

    class Verification:
        def __init__(
            self,
            resolution,
            video_codec,
        ):
            self.resolution = resolution
            self.video_codec = video_codec
            self.changed = True

    verifications = iter(
        [
            Verification(
                "480p",
                "h264",
            ),
            Verification(
                "1080p",
                "h264",
            ),
        ]
    )

    monkeypatch.setattr(
        ui,
        "verify_quality",
        lambda media: next(
            verifications
        ),
    )

    class Preference:
        index = 1
        reason = (
            "higher verified resolution"
        )

    monkeypatch.setattr(
        ui,
        "technical_preference",
        lambda values: Preference(),
    )

    ui._show_duplicate_groups(
        audit
    )

    output = capsys.readouterr().out

    assert (
        output.count(
            "Recommendation: KEEP"
        )
        == 1
    )

    assert (
        output.count(
            "Recommendation: REMOVE"
        )
        == 1
    )

    assert (
        "Preference reason:    "
        "higher verified resolution"
        in output
    )


def test_duplicate_display_has_no_recommendation_when_uncertain(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    first = make_entry(
        tmp_path / "first",
        filename=(
            "Movie (2020) A.mkv"
        ),
        issues={
            LibraryIssue.DUPLICATE_CANDIDATE,
        },
    )

    second = make_entry(
        tmp_path / "second",
        filename=(
            "Movie (2020) B.mkv"
        ),
        issues={
            LibraryIssue.DUPLICATE_CANDIDATE,
        },
    )

    key = (
        "movie",
        "movie",
        2020,
        None,
    )

    audit = LibraryAudit(
        entries=[
            first,
            second,
        ],
        duplicate_groups={
            key: (
                first,
                second,
            ),
        },
        duplicate_classifications={
            key: (
                DuplicateClassification
                .QUALITY_VARIANT
            ),
        },
    )

    monkeypatch.setattr(
        ui,
        "verify_quality",
        lambda media: None,
    )

    monkeypatch.setattr(
        ui,
        "technical_preference",
        lambda values: None,
    )

    ui._show_duplicate_groups(
        audit
    )

    output = capsys.readouterr().out

    assert "Recommendation:" not in output
