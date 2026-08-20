from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.metadata.technical import TechnicalMetadata


class MediaIntegrityStatus(str, Enum):
    HEALTHY = "HEALTHY"
    AUXILIARY = "AUXILIARY"
    SUSPICIOUS = "SUSPICIOUS"
    CORRUPT = "CORRUPT"


@dataclass(frozen=True, slots=True)
class MediaIntegrityResult:
    status: MediaIntegrityStatus
    reasons: tuple[str, ...]

    @property
    def usable_as_primary_media(self) -> bool:
        """
        True only when the file can safely count as the
        normal movie/episode represented by its identity.

        AUXILIARY files may be perfectly valid media, but
        deliberately do not satisfy a normal movie/episode.
        """
        return self.status == MediaIntegrityStatus.HEALTHY

    @property
    def requires_review(self) -> bool:
        return self.status in {
            MediaIntegrityStatus.SUSPICIOUS,
            MediaIntegrityStatus.CORRUPT,
        }


_AUXILIARY_DIRECTORY_NAMES = {
    "bonus",
    "bonus features",
    "deleted scene",
    "deleted scenes",
    "extras",
    "featurette",
    "featurettes",
    "sample",
    "samples",
    "trailer",
    "trailers",
}

_AUXILIARY_FILENAME_MARKERS = (
    "sample",
    "trailer",
    "featurette",
    "deleted scene",
    "deleted scenes",
)


def _path_parts(
    path: Path | None,
) -> tuple[str, ...]:
    if path is None:
        return ()

    return tuple(
        part.casefold().strip()
        for part in path.parts
    )


def _looks_like_appledouble(
    path: Path | None,
) -> bool:
    if path is None:
        return False

    return path.name.startswith("._")


def _looks_auxiliary_by_path(
    path: Path | None,
) -> bool:
    if path is None:
        return False

    parts = _path_parts(path)

    if any(
        part in _AUXILIARY_DIRECTORY_NAMES
        for part in parts[:-1]
    ):
        return True

    stem = path.stem.casefold()

    return any(
        marker in stem
        for marker in _AUXILIARY_FILENAME_MARKERS
    )


def _is_auxiliary_identity(
    media: MediaMetadata,
) -> bool:
    if media.content_type == "extra":
        return True

    return _looks_auxiliary_by_path(
        media.path
    )


def _filesystem_size(
    media: MediaMetadata,
    technical: TechnicalMetadata,
) -> int:
    """
    Prefer the scanner's filesystem size because it is
    available even when ffprobe cannot parse the file.
    """
    if media.size is not None:
        return media.size

    if technical.size is not None:
        return technical.size

    return 0


def _normal_content_duration_is_implausible(
    media: MediaMetadata,
    technical: TechnicalMetadata,
) -> bool:
    duration = technical.duration_seconds

    if duration is None:
        return True

    if duration <= 0:
        return True

    # Deliberately conservative thresholds.
    #
    # The real library has normal TV episode files such as
    # Blindspot S04E15/S04E19 that are only a few seconds
    # long due to truncation. A five-minute floor catches
    # those catastrophic failures while avoiding assumptions
    # about legitimate short-form programming.
    if (
        media.media_type == "tv"
        and media.content_type == "episode"
        and duration < 300
    ):
        return True

    # A file identified as an ordinary feature film but
    # shorter than ten minutes is unlikely to be the actual
    # movie. Samples/trailers are classified AUXILIARY before
    # this rule is reached.
    if (
        media.media_type == "movie"
        and media.content_type == "movie"
        and duration < 600
    ):
        return True

    return False


def classify_media_integrity(
    media: MediaMetadata,
    technical: TechnicalMetadata,
) -> MediaIntegrityResult:
    """
    Interpret filesystem identity + ffprobe facts.

    This function is pure/read-only. It does not modify,
    move, rename, delete, repair, transcode, or refresh
    anything.

    Precedence is intentional:

    1. AppleDouble/resource-fork files are AUXILIARY junk,
       even though ffprobe correctly fails them.
    2. Explicit extras/samples/trailers are AUXILIARY if
       they are technically valid.
    3. Zero-byte and unprobeable normal media are CORRUPT.
    4. Playable but implausibly short normal content is
       SUSPICIOUS.
    5. Everything else is HEALTHY.
    """
    path = media.path

    if _looks_like_appledouble(path):
        return MediaIntegrityResult(
            status=MediaIntegrityStatus.AUXILIARY,
            reasons=(
                "AppleDouble/resource-fork file.",
            ),
        )

    auxiliary = _is_auxiliary_identity(
        media
    )

    size = _filesystem_size(
        media,
        technical,
    )

    if size == 0:
        if auxiliary:
            return MediaIntegrityResult(
                status=(
                    MediaIntegrityStatus
                    .AUXILIARY
                ),
                reasons=(
                    "Auxiliary media entry is zero bytes.",
                ),
            )

        return MediaIntegrityResult(
            status=MediaIntegrityStatus.CORRUPT,
            reasons=(
                "Media file is zero bytes.",
            ),
        )

    if not technical.probe_ok:
        if auxiliary:
            return MediaIntegrityResult(
                status=MediaIntegrityStatus.AUXILIARY,
                reasons=(
                    "Auxiliary media is not probeable.",
                    technical.error
                    or "ffprobe failed.",
                ),
            )

        return MediaIntegrityResult(
            status=MediaIntegrityStatus.CORRUPT,
            reasons=(
                "ffprobe could not read the media.",
                technical.error
                or "Unknown ffprobe failure.",
            ),
        )

    if technical.primary_video is None:
        if auxiliary:
            return MediaIntegrityResult(
                status=MediaIntegrityStatus.AUXILIARY,
                reasons=(
                    "Auxiliary item has no playable video stream.",
                ),
            )

        return MediaIntegrityResult(
            status=MediaIntegrityStatus.CORRUPT,
            reasons=(
                "No playable video stream found.",
            ),
        )

    if auxiliary:
        return MediaIntegrityResult(
            status=MediaIntegrityStatus.AUXILIARY,
            reasons=(
                "Path or identity identifies auxiliary media.",
            ),
        )

    if _normal_content_duration_is_implausible(
        media,
        technical,
    ):
        duration = technical.duration_seconds

        if duration is None:
            reason = (
                "Playable media has no usable duration."
            )
        else:
            reason = (
                "Duration is implausibly short for "
                f"normal {media.content_type}: "
                f"{duration:.2f} seconds."
            )

        return MediaIntegrityResult(
            status=MediaIntegrityStatus.SUSPICIOUS,
            reasons=(reason,),
        )

    return MediaIntegrityResult(
        status=MediaIntegrityStatus.HEALTHY,
        reasons=(
            "Playable media passed integrity checks.",
        ),
    )
