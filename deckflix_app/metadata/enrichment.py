from __future__ import annotations

from dataclasses import replace

from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.technical import TechnicalMetadata


def enrich_quality_from_technical(
    media: MediaMetadata,
    technical: TechnicalMetadata,
) -> MediaMetadata:
    """
    Return MediaMetadata with trustworthy technical quality
    fields updated from an already-completed media probe.

    No probing is performed here.

    ffprobe is authoritative for:
      - resolution
      - video codec

    Release source remains filename-derived because technical
    probing cannot reliably determine whether a file originated
    from BluRay, WEB-DL, WEBRip, DVD, etc.

    Failed probes leave the original metadata unchanged.
    """
    if not technical.probe_ok:
        return media

    resolution = (
        technical.resolution_label
        or media.resolution
    )

    video_codec = (
        technical.video_codec
        or media.video_codec
    )

    if (
        resolution == media.resolution
        and video_codec == media.video_codec
    ):
        return media

    return replace(
        media,
        resolution=resolution,
        video_codec=video_codec,
    )
