from deckflix_app.metadata.enrichment import (
    enrich_quality_from_technical,
)
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.technical import TechnicalMetadata
from deckflix_app.quality import (
    compare_quality,
    quality_score,
)

from .actions import Action
from .models import Decision


def decide(
    existing: MediaMetadata | None,
    incoming: MediaMetadata,
) -> Decision:
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


def decide_with_technical(
    existing: MediaMetadata | None,
    incoming: MediaMetadata,
    *,
    existing_technical: TechnicalMetadata | None = None,
    incoming_technical: TechnicalMetadata | None = None,
) -> Decision:
    """
    Make the normal DeckFlix quality decision using already-probed
    technical metadata when it is available.

    This function does not probe files.

    Successful technical probes may correct resolution and video
    codec before the normal quality comparison. Release source
    remains filename-derived.

    Missing or failed probes preserve the existing filename-based
    decision behaviour.

    Approval policy is deliberately outside this function. In
    particular, an UPGRADE decision still requires operator REVIEW
    under the normal approval policy.
    """
    verified_existing = existing

    if (
        existing is not None
        and existing_technical is not None
    ):
        verified_existing = (
            enrich_quality_from_technical(
                existing,
                existing_technical,
            )
        )

    verified_incoming = incoming

    if incoming_technical is not None:
        verified_incoming = (
            enrich_quality_from_technical(
                incoming,
                incoming_technical,
            )
        )

    return decide(
        verified_existing,
        verified_incoming,
    )
