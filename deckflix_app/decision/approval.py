from dataclasses import dataclass
from enum import Enum

from .actions import Action
from .queue import DecisionQueue, DecisionQueueItem


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

    def count(self, status: ApprovalStatus) -> int:
        return sum(
            1
            for item in self.items
            if item.status is status
        )

    def ready(self) -> list[ApprovalItem]:
        return [
            item
            for item in self.items
            if item.status is ApprovalStatus.READY
        ]

    def approved(self) -> list[ApprovalItem]:
        return [
            item
            for item in self.items
            if item.status is ApprovalStatus.APPROVED
        ]

    def skipped(self) -> list[ApprovalItem]:
        return [
            item
            for item in self.items
            if item.status is ApprovalStatus.SKIPPED
        ]

    def review(self) -> list[ApprovalItem]:
        return [
            item
            for item in self.items
            if item.status is ApprovalStatus.REVIEW
        ]


def default_approval_status(action: Action) -> ApprovalStatus:
    """
    Conservative default approval policy.

    NEW media may be approved automatically.
    Existing-media changes always require operator review.
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


def build_approval_plan(
    queue: DecisionQueue,
) -> ApprovalPlan:
    return ApprovalPlan(
        items=[
            ApprovalItem(
                queue_item=item,
                status=default_approval_status(
                    item.decision.action
                ),
            )
            for item in queue.items
        ]
    )
