from deckflix_app.decision import (
    Action,
    ApprovalStatus,
    build_approval_plan,
    build_decision_queue,
    default_approval_status,
)
from deckflix_app.metadata.models import MediaMetadata


def movie(
    title: str,
    year: int,
    resolution: str,
) -> MediaMetadata:
    return MediaMetadata(
        media_type="movie",
        title=title,
        year=year,
        resolution=resolution,
        source="BluRay",
        video_codec="HEVC",
    )


def test_new_media_is_ready_by_default():
    assert (
        default_approval_status(Action.NEW)
        is ApprovalStatus.READY
    )


def test_upgrade_requires_review():
    assert (
        default_approval_status(Action.UPGRADE)
        is ApprovalStatus.REVIEW
    )


def test_duplicate_is_skipped():
    assert (
        default_approval_status(Action.DUPLICATE)
        is ApprovalStatus.SKIPPED
    )


def test_downgrade_is_skipped():
    assert (
        default_approval_status(Action.DOWNGRADE)
        is ApprovalStatus.SKIPPED
    )


def test_approval_plan_summary():
    queue = build_decision_queue(
        incoming=[
            movie("Alien", 1979, "1080p"),
            movie("Avatar", 2009, "1080p"),
            movie("Dune", 2021, "2160p"),
        ],
        library=[
            movie("Avatar", 2009, "1080p"),
            movie("Dune", 2021, "1080p"),
        ],
    )

    plan = build_approval_plan(queue)

    assert plan.total == 3
    assert plan.count(ApprovalStatus.READY) == 1
    assert plan.count(ApprovalStatus.APPROVED) == 0
    assert plan.count(ApprovalStatus.SKIPPED) == 1
    assert plan.count(ApprovalStatus.REVIEW) == 1
    assert len(plan.ready()) == 1
    assert len(plan.approved()) == 0
    assert len(plan.skipped()) == 1
    assert len(plan.review()) == 1
