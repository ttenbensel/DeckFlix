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


def test_review_item_can_be_approved():
    from deckflix_app.decision import (
        ApprovalStatus,
    )

    queue = build_decision_queue(
        incoming=[
            movie(
                "Dune",
                2021,
                "2160p",
            ),
        ],
        library=[
            movie(
                "Dune",
                2021,
                "1080p",
            ),
        ],
    )

    plan = build_approval_plan(queue)

    assert len(plan.review()) == 1

    item = plan.review()[0]

    result = plan.approve_review(item)

    assert result is item
    assert item.status is ApprovalStatus.APPROVED
    assert len(plan.review()) == 0
    assert len(plan.approved()) == 1


def test_review_item_can_be_skipped():
    from deckflix_app.decision import (
        ApprovalStatus,
    )

    queue = build_decision_queue(
        incoming=[
            movie(
                "Dune",
                2021,
                "2160p",
            ),
        ],
        library=[
            movie(
                "Dune",
                2021,
                "1080p",
            ),
        ],
    )

    plan = build_approval_plan(queue)

    item = plan.review()[0]

    result = plan.skip_review(item)

    assert result is item
    assert item.status is ApprovalStatus.SKIPPED
    assert len(plan.review()) == 0
    assert len(plan.skipped()) == 1


def test_non_review_item_cannot_be_resolved():
    import pytest

    from deckflix_app.decision import (
        ApprovalStatus,
        InvalidApprovalResolution,
    )

    queue = build_decision_queue(
        incoming=[
            movie(
                "Alien",
                1979,
                "1080p",
            ),
        ],
        library=[],
    )

    plan = build_approval_plan(queue)

    item = plan.ready()[0]

    with pytest.raises(
        InvalidApprovalResolution,
        match="Only REVIEW items",
    ):
        plan.resolve_review(
            item,
            ApprovalStatus.APPROVED,
        )

    assert item.status is ApprovalStatus.READY


def test_review_item_rejects_invalid_resolution():
    import pytest

    from deckflix_app.decision import (
        ApprovalStatus,
        InvalidApprovalResolution,
    )

    queue = build_decision_queue(
        incoming=[
            movie(
                "Dune",
                2021,
                "2160p",
            ),
        ],
        library=[
            movie(
                "Dune",
                2021,
                "1080p",
            ),
        ],
    )

    plan = build_approval_plan(queue)

    item = plan.review()[0]

    with pytest.raises(
        InvalidApprovalResolution,
        match="APPROVED or SKIPPED",
    ):
        plan.resolve_review(
            item,
            ApprovalStatus.READY,
        )

    assert item.status is ApprovalStatus.REVIEW


def test_review_item_from_other_plan_is_rejected():
    import pytest

    from deckflix_app.decision import (
        InvalidApprovalResolution,
    )

    first_queue = build_decision_queue(
        incoming=[
            movie(
                "Dune",
                2021,
                "2160p",
            ),
        ],
        library=[
            movie(
                "Dune",
                2021,
                "1080p",
            ),
        ],
    )

    second_queue = build_decision_queue(
        incoming=[
            movie(
                "Avatar",
                2009,
                "2160p",
            ),
        ],
        library=[
            movie(
                "Avatar",
                2009,
                "1080p",
            ),
        ],
    )

    first_plan = build_approval_plan(
        first_queue
    )
    second_plan = build_approval_plan(
        second_queue
    )

    foreign_item = (
        second_plan.review()[0]
    )

    with pytest.raises(
        InvalidApprovalResolution,
        match="does not belong",
    ):
        first_plan.approve_review(
            foreign_item
        )
