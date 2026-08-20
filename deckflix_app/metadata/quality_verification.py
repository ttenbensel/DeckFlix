from __future__ import annotations

from dataclasses import dataclass

from deckflix_app.metadata.enrichment import (
    enrich_quality_from_technical,
)
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.probe import probe_media


@dataclass(frozen=True, slots=True)
class QualityVerification:
    resolution: str | None
    video_codec: str | None
    changed: bool


@dataclass(frozen=True, slots=True)
class TechnicalPreference:
    index: int
    reason: str


def verify_quality(
    media: MediaMetadata,
) -> QualityVerification | None:
    """
    Read technical resolution and codec for display purposes.

    This helper is read-only.

    It does not alter the supplied MediaMetadata object and does
    not participate in duplicate classification, quality ranking,
    repair planning, or import decisions.

    A failed probe produces no verification display.
    """
    if media.path is None:
        return None

    technical = probe_media(
        media.path
    )

    if not technical.probe_ok:
        return None

    enriched = enrich_quality_from_technical(
        media,
        technical,
    )

    changed = (
        enriched.resolution
        != media.resolution
        or enriched.video_codec
        != media.video_codec
    )

    return QualityVerification(
        resolution=enriched.resolution,
        video_codec=enriched.video_codec,
        changed=changed,
    )


def _resolution_rank(
    value: str | None,
) -> int:
    ranks = {
        "sd": 1,
        "360p": 2,
        "480p": 3,
        "720p": 4,
        "1080p": 5,
        "2160p": 6,
    }

    if value is None:
        return 0

    return ranks.get(
        value.casefold(),
        0,
    )


def _codec_rank(
    value: str | None,
) -> int:
    if value is None:
        return 0

    value = value.casefold()

    if value in {
        "av1",
    }:
        return 3

    if value in {
        "hevc",
        "h265",
        "x265",
    }:
        return 2

    if value in {
        "h264",
        "x264",
    }:
        return 1

    return 0


def technical_preference(
    verifications: list[
        QualityVerification | None
    ],
) -> TechnicalPreference | None:
    """
    Return one clear verified technical preference.

    Resolution is compared first. Codec is only used as a
    tie-breaker when resolution is equal.

    Missing or failed verification never creates a preference.

    This is informational only.
    """
    candidates = []

    for index, verification in enumerate(
        verifications
    ):
        if verification is None:
            continue

        resolution_rank = _resolution_rank(
            verification.resolution
        )

        if resolution_rank == 0:
            continue

        candidates.append(
            (
                index,
                resolution_rank,
                _codec_rank(
                    verification.video_codec
                ),
                verification,
            )
        )

    if len(candidates) < 2:
        return None

    best_resolution = max(
        item[1]
        for item in candidates
    )

    resolution_winners = [
        item
        for item in candidates
        if item[1] == best_resolution
    ]

    if len(resolution_winners) == 1:
        winner = resolution_winners[0]

        return TechnicalPreference(
            index=winner[0],
            reason=(
                "higher verified resolution"
            ),
        )

    best_codec = max(
        item[2]
        for item in resolution_winners
    )

    if best_codec == 0:
        return None

    codec_winners = [
        item
        for item in resolution_winners
        if item[2] == best_codec
    ]

    if len(codec_winners) != 1:
        return None

    if all(
        item[2] == best_codec
        for item in resolution_winners
    ):
        return None

    winner = codec_winners[0]

    return TechnicalPreference(
        index=winner[0],
        reason=(
            "same verified resolution, "
            "preferred video codec"
        ),
    )
