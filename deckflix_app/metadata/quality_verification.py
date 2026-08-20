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
