from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, frozen=True)
class VideoStreamMetadata:
    index: int
    codec: str | None = None
    codec_long_name: str | None = None
    profile: str | None = None

    width: int | None = None
    height: int | None = None

    pixel_format: str | None = None
    bit_depth: int | None = None

    level: int | None = None
    bit_rate: int | None = None

    color_range: str | None = None
    color_space: str | None = None
    color_transfer: str | None = None
    color_primaries: str | None = None

    hdr: bool = False


@dataclass(slots=True, frozen=True)
class AudioStreamMetadata:
    index: int
    codec: str | None = None
    codec_long_name: str | None = None
    profile: str | None = None

    channels: int | None = None
    channel_layout: str | None = None
    sample_rate: int | None = None
    bit_rate: int | None = None

    language: str | None = None
    title: str | None = None


@dataclass(slots=True, frozen=True)
class SubtitleStreamMetadata:
    index: int
    codec: str | None = None
    codec_long_name: str | None = None

    language: str | None = None
    title: str | None = None


@dataclass(slots=True)
class TechnicalMetadata:
    path: Path

    probe_ok: bool
    error: str | None = None

    format_name: str | None = None
    duration_seconds: float | None = None
    size: int | None = None
    bit_rate: int | None = None

    primary_video: VideoStreamMetadata | None = None

    video_streams: list[VideoStreamMetadata] = field(
        default_factory=list
    )
    audio_streams: list[AudioStreamMetadata] = field(
        default_factory=list
    )
    subtitle_streams: list[SubtitleStreamMetadata] = field(
        default_factory=list
    )

    @property
    def width(self) -> int | None:
        if self.primary_video is None:
            return None

        return self.primary_video.width

    @property
    def height(self) -> int | None:
        if self.primary_video is None:
            return None

        return self.primary_video.height

    @property
    def video_codec(self) -> str | None:
        if self.primary_video is None:
            return None

        return self.primary_video.codec

    @property
    def bit_depth(self) -> int | None:
        if self.primary_video is None:
            return None

        return self.primary_video.bit_depth

    @property
    def hdr(self) -> bool:
        if self.primary_video is None:
            return False

        return self.primary_video.hdr

    @property
    def resolution_label(self) -> str | None:
        """
        Return a conventional resolution class while preserving
        exact width/height separately.

        Widescreen cinema encodes such as 1920x800 still belong
        to the 1080-class source family despite cropped vertical
        dimensions.
        """
        width = self.width
        height = self.height

        if width is None or height is None:
            return None

        if width >= 3800 or height >= 2000:
            return "2160p"

        if width >= 1900 or height >= 1000:
            return "1080p"

        if width >= 1260 or height >= 700:
            return "720p"

        if width >= 700 or height >= 470:
            return "480p"

        if width >= 620 or height >= 350:
            return "360p"

        return "SD"
