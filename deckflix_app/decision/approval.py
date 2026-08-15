from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re

from .actions import Action
from .queue import (
    DecisionQueue,
    DecisionQueueItem,
)


class ApprovalStatus(str, Enum):
    READY = "READY"
    APPROVED = "APPROVED"
    SKIPPED = "SKIPPED"
    REVIEW = "REVIEW"


@dataclass(slots=True)
class ApprovalItem:
    queue_item: DecisionQueueItem
    status: ApprovalStatus

    @property
    def action(self) -> Action:
        return self.queue_item.decision.action


@dataclass(slots=True)
class ApprovalPlan:
    items: list[ApprovalItem]

    @property
    def total(self) -> int:
        return len(self.items)

    def count(
        self,
        status: ApprovalStatus,
    ) -> int:
        return sum(
            1
            for item in self.items
            if item.status is status
        )

    def ready(self) -> list[ApprovalItem]:
        return [
            item
            for item in self.items
            if item.status
            is ApprovalStatus.READY
        ]

    def approved(self) -> list[ApprovalItem]:
        return [
            item
            for item in self.items
            if item.status
            is ApprovalStatus.APPROVED
        ]

    def skipped(self) -> list[ApprovalItem]:
        return [
            item
            for item in self.items
            if item.status
            is ApprovalStatus.SKIPPED
        ]

    def review(self) -> list[ApprovalItem]:
        return [
            item
            for item in self.items
            if item.status
            is ApprovalStatus.REVIEW
        ]


def default_approval_status(
    action: Action,
) -> ApprovalStatus:
    """
    Conservative default approval policy.

    NEW media may become READY only after the
    additional identity-safety checks performed by
    build_approval_plan().

    Existing-media changes always require operator
    review.

    Equivalent or worse incoming copies are skipped.
    """
    if action is Action.NEW:
        return ApprovalStatus.READY

    if action is Action.UPGRADE:
        return ApprovalStatus.REVIEW

    if action in {
        Action.DUPLICATE,
        Action.DOWNGRADE,
    }:
        return ApprovalStatus.SKIPPED

    return ApprovalStatus.REVIEW


def _normalised_identity(
    item: DecisionQueueItem,
) -> tuple:
    media = item.incoming

    return (
        media.media_type,
        (media.title or "").strip().casefold(),
        media.year,
        media.season,
        media.episode,
    )


def _path_text(
    item: DecisionQueueItem,
) -> str:
    path = item.incoming.path

    if path is None:
        return ""

    return str(
        Path(path)
    )


def _looks_like_unresolved_tv(
    item: DecisionQueueItem,
) -> bool:
    """
    Detect media classified as a movie even though its
    filesystem path strongly suggests TV, specials, or
    bonus material.

    These items are not rejected. They are routed to
    operator REVIEW instead of being automatically
    approved as NEW media.

    A missing path alone is not considered suspicious.
    Import preflight separately validates source paths.
    """
    media = item.incoming

    if media.media_type != "movie":
        return False

    text = _path_text(
        item
    )

    if not text:
        return False

    lower = text.casefold()

    extra_terms = (
        "extras",
        "extra",
        "minisode",
        "deleted scene",
        "behind the scenes",
        "gag reel",
        "featurette",
        "making of",
    )

    if any(
        term in lower
        for term in extra_terms
    ):
        return True

    # Movie-classified content inside an explicit
    # Season directory is suspicious.
    if re.search(
        r"""
        (?:^|[/\\])
        season[ ._-]*\d{1,2}
        (?:[/\\]|$)
        """,
        text,
        re.IGNORECASE | re.VERBOSE,
    ):
        return True

    stem = Path(
        text
    ).stem

    # Episode 01
    if re.search(
        r"\bepisode[ ._-]*\d{1,3}\b",
        stem,
        re.IGNORECASE,
    ):
        return True

    # Part 01 / Part.1
    #
    # This is deliberately REVIEW-only. We do not
    # automatically equate Part 01 with S01E01,
    # because multipart movies also exist.
    if re.search(
        r"\bpart[ ._-]*\d{1,3}\b",
        stem,
        re.IGNORECASE,
    ):
        return True

    # S05M01 and similar usually represent specials,
    # TV movies, or collection material rather than a
    # conventional episode.
    if re.search(
        r"\b[Ss]\d{1,2}[Mm]\d{1,3}\b",
        stem,
    ):
        return True

    # Bare E01 occurring in a path that contains an
    # explicit season marker is TV-like.
    if (
        re.search(
            r"\b[Ee]\d{1,3}\b",
            stem,
        )
        and re.search(
            r"\b[Ss]\d{1,2}\b",
            text,
        )
    ):
        return True

    # Old scene-style episode numbering such as:
    #
    # scorpion.117.hdtv-lol
    # masters.of.sex.303.hdtv-lol
    #
    # Only apply this safety rule when the enclosing
    # path explicitly states a Season directory.
    if (
        re.search(
            r"(?:^|[._ -])\d{3}(?:[._ -]|$)",
            stem,
        )
        and re.search(
            r"""
            (?:^|[/\\])
            season[ ._-]*\d{1,2}
            (?:[/\\]|$)
            """,
            text,
            re.IGNORECASE | re.VERBOSE,
        )
    ):
        return True

    return False


def build_approval_plan(
    queue: DecisionQueue,
) -> ApprovalPlan:
    """
    Build the approval plan with a fail-safe NEW-media
    gate.

    NEW media is automatically READY only when its
    identity appears unambiguous.

    NEW items are forced to REVIEW when:

    - multiple NEW queue entries collapse to the same
      normalised identity, or
    - the parser classified something as a movie even
      though its filesystem path strongly resembles TV,
      extras, specials, or multipart episodic content.

    This prevents imperfect legacy filename parsing
    from automatically writing ambiguous media into
    the main library.
    """
    new_identity_counts: dict[
        tuple,
        int,
    ] = {}

    for item in queue.items:
        if (
            item.decision.action
            is not Action.NEW
        ):
            continue

        identity = _normalised_identity(
            item
        )

        new_identity_counts[
            identity
        ] = (
            new_identity_counts.get(
                identity,
                0,
            )
            + 1
        )

    approval_items = []

    for item in queue.items:
        status = default_approval_status(
            item.decision.action
        )

        if (
            item.decision.action
            is Action.NEW
        ):
            identity = _normalised_identity(
                item
            )

            identity_collision = (
                new_identity_counts.get(
                    identity,
                    0,
                )
                > 1
            )

            unresolved_tv = (
                _looks_like_unresolved_tv(
                    item
                )
            )

            if (
                identity_collision
                or unresolved_tv
            ):
                status = (
                    ApprovalStatus.REVIEW
                )

        approval_items.append(
            ApprovalItem(
                queue_item=item,
                status=status,
            )
        )

    return ApprovalPlan(
        items=approval_items
    )
