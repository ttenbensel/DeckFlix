from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
from typing import Any

from .technical import (
    AudioStreamMetadata,
    SubtitleStreamMetadata,
    TechnicalMetadata,
    VideoStreamMetadata,
)


_IMAGE_VIDEO_CODECS = {
    "apng",
    "bmp",
    "gif",
    "mjpeg",
    "mjpegb",
    "png",
    "targa",
    "tiff",
    "webp",
}


_HDR_TRANSFERS = {
    "arib-std-b67",
    "smpte2084",
}


def _optional_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    if text.casefold() in {
        "n/a",
        "unknown",
    }:
        return None

    return text


def _optional_int(
    value: Any,
) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bit_depth(
    stream: dict[str, Any],
) -> int | None:
    explicit = _optional_int(
        stream.get(
            "bits_per_raw_sample"
        )
    )

    if explicit is not None and explicit > 0:
        return explicit

    pixel_format = _optional_text(
        stream.get("pix_fmt")
    )

    if pixel_format is None:
        return None

    match = re.search(
        r"(?:p|gbrp|gray)(\d{2})(?:le|be)?$",
        pixel_format.casefold(),
    )

    if match is not None:
        return int(match.group(1))

    if pixel_format.casefold() in {
        "yuv420p",
        "yuv422p",
        "yuv444p",
        "nv12",
        "nv21",
        "rgb24",
        "bgr24",
    }:
        return 8

    return None


def _is_hdr(
    stream: dict[str, Any],
) -> bool:
    transfer = (
        _optional_text(
            stream.get("color_transfer")
        )
        or ""
    ).casefold()

    primaries = (
        _optional_text(
            stream.get("color_primaries")
        )
        or ""
    ).casefold()

    return (
        transfer in _HDR_TRANSFERS
        or (
            primaries == "bt2020"
            and transfer not in {
                "",
                "bt709",
            }
        )
    )


def _video_stream(
    stream: dict[str, Any],
) -> VideoStreamMetadata:
    return VideoStreamMetadata(
        index=(
            _optional_int(
                stream.get("index")
            )
            or 0
        ),
        codec=_optional_text(
            stream.get("codec_name")
        ),
        codec_long_name=_optional_text(
            stream.get(
                "codec_long_name"
            )
        ),
        profile=_optional_text(
            stream.get("profile")
        ),
        width=_optional_int(
            stream.get("width")
        ),
        height=_optional_int(
            stream.get("height")
        ),
        pixel_format=_optional_text(
            stream.get("pix_fmt")
        ),
        bit_depth=_bit_depth(
            stream
        ),
        level=_optional_int(
            stream.get("level")
        ),
        bit_rate=_optional_int(
            stream.get("bit_rate")
        ),
        color_range=_optional_text(
            stream.get("color_range")
        ),
        color_space=_optional_text(
            stream.get("color_space")
        ),
        color_transfer=_optional_text(
            stream.get(
                "color_transfer"
            )
        ),
        color_primaries=_optional_text(
            stream.get(
                "color_primaries"
            )
        ),
        hdr=_is_hdr(
            stream
        ),
    )


def _audio_stream(
    stream: dict[str, Any],
) -> AudioStreamMetadata:
    tags = stream.get("tags")

    if not isinstance(tags, dict):
        tags = {}

    return AudioStreamMetadata(
        index=(
            _optional_int(
                stream.get("index")
            )
            or 0
        ),
        codec=_optional_text(
            stream.get("codec_name")
        ),
        codec_long_name=_optional_text(
            stream.get(
                "codec_long_name"
            )
        ),
        profile=_optional_text(
            stream.get("profile")
        ),
        channels=_optional_int(
            stream.get("channels")
        ),
        channel_layout=_optional_text(
            stream.get(
                "channel_layout"
            )
        ),
        sample_rate=_optional_int(
            stream.get(
                "sample_rate"
            )
        ),
        bit_rate=_optional_int(
            stream.get("bit_rate")
        ),
        language=_optional_text(
            tags.get("language")
        ),
        title=_optional_text(
            tags.get("title")
        ),
    )


def _subtitle_stream(
    stream: dict[str, Any],
) -> SubtitleStreamMetadata:
    tags = stream.get("tags")

    if not isinstance(tags, dict):
        tags = {}

    return SubtitleStreamMetadata(
        index=(
            _optional_int(
                stream.get("index")
            )
            or 0
        ),
        codec=_optional_text(
            stream.get("codec_name")
        ),
        codec_long_name=_optional_text(
            stream.get(
                "codec_long_name"
            )
        ),
        language=_optional_text(
            tags.get("language")
        ),
        title=_optional_text(
            tags.get("title")
        ),
    )


def _primary_video(
    streams: list[VideoStreamMetadata],
) -> VideoStreamMetadata | None:
    """
    Choose the first playable video stream.

    ffprobe can report artwork/image streams as video. Those
    must not become the authoritative movie resolution merely
    because their dimensions are larger than the actual video.
    """
    for stream in streams:
        codec = (
            stream.codec
            or ""
        ).casefold()

        if codec not in _IMAGE_VIDEO_CODECS:
            return stream

    return None


def technical_metadata_from_payload(
    path: str | Path,
    payload: dict[str, Any],
) -> TechnicalMetadata:
    media_path = Path(path)

    raw_streams = payload.get(
        "streams"
    )

    if not isinstance(raw_streams, list):
        raw_streams = []

    videos: list[VideoStreamMetadata] = []
    audios: list[AudioStreamMetadata] = []
    subtitles: list[SubtitleStreamMetadata] = []

    for raw_stream in raw_streams:
        if not isinstance(
            raw_stream,
            dict,
        ):
            continue

        stream_type = (
            _optional_text(
                raw_stream.get(
                    "codec_type"
                )
            )
            or ""
        ).casefold()

        if stream_type == "video":
            videos.append(
                _video_stream(
                    raw_stream
                )
            )

        elif stream_type == "audio":
            audios.append(
                _audio_stream(
                    raw_stream
                )
            )

        elif stream_type == "subtitle":
            subtitles.append(
                _subtitle_stream(
                    raw_stream
                )
            )

    raw_format = payload.get(
        "format"
    )

    if not isinstance(raw_format, dict):
        raw_format = {}

    primary = _primary_video(
        videos
    )

    if primary is None:
        return TechnicalMetadata(
            path=media_path,
            probe_ok=False,
            error=(
                "No playable video stream found."
            ),
            format_name=_optional_text(
                raw_format.get(
                    "format_name"
                )
            ),
            duration_seconds=_optional_float(
                raw_format.get(
                    "duration"
                )
            ),
            size=_optional_int(
                raw_format.get("size")
            ),
            bit_rate=_optional_int(
                raw_format.get(
                    "bit_rate"
                )
            ),
            video_streams=videos,
            audio_streams=audios,
            subtitle_streams=subtitles,
        )

    return TechnicalMetadata(
        path=media_path,
        probe_ok=True,
        format_name=_optional_text(
            raw_format.get(
                "format_name"
            )
        ),
        duration_seconds=_optional_float(
            raw_format.get(
                "duration"
            )
        ),
        size=_optional_int(
            raw_format.get("size")
        ),
        bit_rate=_optional_int(
            raw_format.get(
                "bit_rate"
            )
        ),
        primary_video=primary,
        video_streams=videos,
        audio_streams=audios,
        subtitle_streams=subtitles,
    )


def probe_media(
    path: str | Path,
    *,
    timeout: float = 30.0,
    ffprobe_binary: str = "ffprobe",
) -> TechnicalMetadata:
    """
    Read technical media metadata with ffprobe.

    This function is read-only. It does not modify, transcode,
    rename, move, copy, delete, or write metadata into media.
    """
    media_path = Path(path)

    command = [
        ffprobe_binary,
        "-v",
        "error",
        "-show_entries",
        (
            "stream=index,codec_type,codec_name,"
            "codec_long_name,profile,width,height,"
            "pix_fmt,level,color_range,color_space,"
            "color_transfer,color_primaries,"
            "bits_per_raw_sample,bit_rate,"
            "channels,channel_layout,sample_rate:"
            "stream_tags=language,title:"
            "format=format_name,duration,size,bit_rate"
        ),
        "-of",
        "json",
        str(media_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )

    except FileNotFoundError:
        return TechnicalMetadata(
            path=media_path,
            probe_ok=False,
            error=(
                f"ffprobe executable not found: "
                f"{ffprobe_binary}"
            ),
        )

    except subprocess.TimeoutExpired:
        return TechnicalMetadata(
            path=media_path,
            probe_ok=False,
            error=(
                f"ffprobe timed out after "
                f"{timeout:g} seconds."
            ),
        )

    except OSError as exc:
        return TechnicalMetadata(
            path=media_path,
            probe_ok=False,
            error=str(exc),
        )

    if result.returncode != 0:
        error = (
            result.stderr.strip()
            or (
                "ffprobe failed with exit "
                f"code {result.returncode}."
            )
        )

        return TechnicalMetadata(
            path=media_path,
            probe_ok=False,
            error=error,
        )

    try:
        payload = json.loads(
            result.stdout
        )

    except json.JSONDecodeError as exc:
        return TechnicalMetadata(
            path=media_path,
            probe_ok=False,
            error=(
                "ffprobe returned invalid JSON: "
                f"{exc}"
            ),
        )

    if not isinstance(payload, dict):
        return TechnicalMetadata(
            path=media_path,
            probe_ok=False,
            error=(
                "ffprobe returned an unexpected "
                "JSON structure."
            ),
        )

    return technical_metadata_from_payload(
        media_path,
        payload,
    )
