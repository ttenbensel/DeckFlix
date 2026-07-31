from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.quality import compare_quality, quality_score

from .actions import Action
from .models import Decision


def decide(existing: MediaMetadata | None, incoming: MediaMetadata) -> Decision:
    incoming_score = quality_score(incoming)

    if existing is None:
        return Decision(
            action=Action.NEW,
            reason="No existing copy",
            existing_score=0,
            incoming_score=incoming_score,
        )

    existing_score = quality_score(existing)

    match compare_quality(existing, incoming):
        case 1:
            return Decision(
                action=Action.UPGRADE,
                reason="Incoming file is higher quality",
                existing_score=existing_score,
                incoming_score=incoming_score,
            )

        case -1:
            return Decision(
                action=Action.DOWNGRADE,
                reason="Existing copy is higher quality",
                existing_score=existing_score,
                incoming_score=incoming_score,
            )

        case _:
            return Decision(
                action=Action.DUPLICATE,
                reason="Quality is equivalent",
                existing_score=existing_score,
                incoming_score=incoming_score,
            )
