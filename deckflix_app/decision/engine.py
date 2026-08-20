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


_VERIFIED_RESOLUTION_RANK = {
    "sd": 1,
    "360p": 2,
    "480p": 3,
    "720p": 4,
    "1080p": 5,
    "2160p": 6,
}


_VERIFIED_CODEC_RANK = {
    "h264": 1,
    "x264": 1,
    "avc": 1,
    "hevc": 2,
    "h265": 2,
    "x265": 2,
    "av1": 3,
}


def _verified_resolution_rank(
    value: str | None,
) -> int:
    if value is None:
        return 0

    return _VERIFIED_RESOLUTION_RANK.get(
        value.casefold(),
        0,
    )


def _verified_codec_rank(
    value: str | None,
) -> int:
    if value is None:
        return 0

    return _VERIFIED_CODEC_RANK.get(
        value.casefold(),
        0,
    )


def _compare_verified_quality(
    existing: MediaMetadata,
    incoming: MediaMetadata,
) -> int:
    """
    Compare two technically verified media candidates.

    Returns:

      1  -> incoming is better
      0  -> technically equivalent
     -1  -> existing is better

    Verified resolution is authoritative and compared first.

    Verified codec is used only when verified resolution is equal.

    Filename-derived release source is deliberately excluded from
    this comparison. Once both files have been successfully probed,
    labels such as Remux, BluRay, WEB-DL, and WEBRip must not create
    a quality difference when the verified technical quality is
    otherwise equivalent.
    """
    existing_resolution = _verified_resolution_rank(
        existing.resolution
    )
    incoming_resolution = _verified_resolution_rank(
        incoming.resolution
    )

    if incoming_resolution > existing_resolution:
        return 1

    if incoming_resolution < existing_resolution:
        return -1

    existing_codec = _verified_codec_rank(
        existing.video_codec
    )
    incoming_codec = _verified_codec_rank(
        incoming.video_codec
    )

    if incoming_codec > existing_codec:
        return 1

    if incoming_codec < existing_codec:
        return -1

    return 0


def decide(
    existing: MediaMetadata | None,
    incoming: MediaMetadata,
) -> Decision:
    incoming_score = quality_score(
        incoming
    )

    if existing is None:
        return Decision(
            action=Action.NEW,
            reason="No existing copy",
            existing_score=0,
            incoming_score=incoming_score,
        )

    existing_score = quality_score(
        existing
    )

    match compare_quality(
        existing,
        incoming,
    ):
        case 1:
            return Decision(
                action=Action.UPGRADE,
                reason=(
                    "Incoming file is higher quality"
                ),
                existing_score=existing_score,
                incoming_score=incoming_score,
            )

        case -1:
            return Decision(
                action=Action.DOWNGRADE,
                reason=(
                    "Existing copy is higher quality"
                ),
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
    Make a DeckFlix quality decision using already-probed technical
    metadata when it is available.

    This function does not probe files.

    NEW media remains NEW.

    When BOTH existing and incoming probes succeed:

      1. verified resolution is compared first;
      2. verified codec breaks an equal-resolution tie;
      3. equal verified resolution and codec are DUPLICATE;
      4. filename-derived release source does not break a verified
         technical tie.

    When only one side has a successful probe, that side is enriched
    with its verified resolution/codec and the normal DeckFlix
    filename-quality decision is then used.

    This preserves the established behavior where trustworthy
    one-sided technical evidence can correct a misleading filename,
    while avoiding source-label asymmetry when both sides have been
    technically verified.

    Failed probes leave that side unchanged.

    Approval policy remains outside this function.
    """
    if existing is None:
        return decide(
            existing,
            incoming,
        )

    existing_verified = (
        existing_technical is not None
        and existing_technical.probe_ok
    )

    incoming_verified = (
        incoming_technical is not None
        and incoming_technical.probe_ok
    )

    if (
        existing_verified
        and incoming_verified
    ):
        verified_existing = (
            enrich_quality_from_technical(
                existing,
                existing_technical,
            )
        )

        verified_incoming = (
            enrich_quality_from_technical(
                incoming,
                incoming_technical,
            )
        )

        existing_score = quality_score(
            verified_existing
        )

        incoming_score = quality_score(
            verified_incoming
        )

        comparison = (
            _compare_verified_quality(
                verified_existing,
                verified_incoming,
            )
        )

        if comparison > 0:
            return Decision(
                action=Action.UPGRADE,
                reason=(
                    "Incoming file has higher verified "
                    "technical quality"
                ),
                existing_score=existing_score,
                incoming_score=incoming_score,
            )

        if comparison < 0:
            return Decision(
                action=Action.DOWNGRADE,
                reason=(
                    "Existing copy has higher verified "
                    "technical quality"
                ),
                existing_score=existing_score,
                incoming_score=incoming_score,
            )

        return Decision(
            action=Action.DUPLICATE,
            reason=(
                "Verified technical quality is equivalent"
            ),
            existing_score=existing_score,
            incoming_score=incoming_score,
        )

    verified_existing = existing

    if existing_technical is not None:
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
