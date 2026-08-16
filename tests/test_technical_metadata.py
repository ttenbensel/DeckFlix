import json
from pathlib import Path
import subprocess

from deckflix_app.metadata.probe import (
    probe_media,
    technical_metadata_from_payload,
)


def test_av1_10_bit_media_is_parsed():
    payload = {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "av1",
                "profile": "Main",
                "width": 1920,
                "height": 1080,
                "pix_fmt": "yuv420p10le",
                "color_space": "bt709",
                "color_transfer": "bt709",
                "color_primaries": "bt709",
            },
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "eac3",
                "channels": 6,
                "channel_layout": "5.1(side)",
                "sample_rate": "48000",
                "bit_rate": "640000",
                "tags": {
                    "language": "eng",
                    "title": "English",
                },
            },
        ],
        "format": {
            "format_name": "matroska,webm",
            "duration": "9676.384000",
            "size": "5837323984",
            "bit_rate": "4826037",
        },
    }

    media = technical_metadata_from_payload(
        "/media/movie.mkv",
        payload,
    )

    assert media.probe_ok is True
    assert media.video_codec == "av1"
    assert media.width == 1920
    assert media.height == 1080
    assert media.bit_depth == 10
    assert media.hdr is False
    assert media.resolution_label == "1080p"

    assert len(media.audio_streams) == 1
    assert media.audio_streams[0].codec == "eac3"
    assert media.audio_streams[0].channels == 6
    assert media.audio_streams[0].language == "eng"


def test_image_stream_is_not_selected_as_primary_video():
    payload = {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "av1",
                "width": 1920,
                "height": 1080,
                "pix_fmt": "yuv420p10le",
            },
            {
                "index": 6,
                "codec_type": "video",
                "codec_name": "png",
                "width": 3840,
                "height": 2160,
                "pix_fmt": "rgb24",
            },
        ],
        "format": {},
    }

    media = technical_metadata_from_payload(
        "/media/movie.mkv",
        payload,
    )

    assert media.probe_ok is True
    assert len(media.video_streams) == 2
    assert media.primary_video is not None
    assert media.primary_video.index == 0
    assert media.width == 1920
    assert media.height == 1080
    assert media.resolution_label == "1080p"


def test_cropped_1920_video_is_1080_class():
    payload = {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "hevc",
                "width": 1920,
                "height": 800,
                "pix_fmt": "yuv420p",
            },
        ],
        "format": {},
    }

    media = technical_metadata_from_payload(
        "/media/movie.mkv",
        payload,
    )

    assert media.width == 1920
    assert media.height == 800
    assert media.resolution_label == "1080p"


def test_old_640x368_video_is_360_class():
    payload = {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "mpeg4",
                "width": 640,
                "height": 368,
                "pix_fmt": "yuv420p",
            },
        ],
        "format": {},
    }

    media = technical_metadata_from_payload(
        "/media/movie.avi",
        payload,
    )

    assert media.video_codec == "mpeg4"
    assert media.resolution_label == "360p"


def test_hdr10_is_detected():
    payload = {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "hevc",
                "width": 3840,
                "height": 2160,
                "pix_fmt": "yuv420p10le",
                "color_primaries": "bt2020",
                "color_transfer": "smpte2084",
            },
        ],
        "format": {},
    }

    media = technical_metadata_from_payload(
        "/media/movie.mkv",
        payload,
    )

    assert media.hdr is True
    assert media.bit_depth == 10
    assert media.resolution_label == "2160p"


def test_subtitle_metadata_is_parsed():
    payload = {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
            },
            {
                "index": 3,
                "codec_type": "subtitle",
                "codec_name": "subrip",
                "tags": {
                    "language": "eng",
                    "title": "English CC",
                },
            },
        ],
        "format": {},
    }

    media = technical_metadata_from_payload(
        "/media/movie.mkv",
        payload,
    )

    assert len(media.subtitle_streams) == 1
    assert media.subtitle_streams[0].codec == "subrip"
    assert media.subtitle_streams[0].language == "eng"
    assert media.subtitle_streams[0].title == "English CC"


def test_probe_failure_is_safe(monkeypatch):
    class Result:
        returncode = 1
        stdout = ""
        stderr = "moov atom not found"

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: Result(),
    )

    media = probe_media(
        "/media/broken.mp4"
    )

    assert media.probe_ok is False
    assert media.error is not None
    assert "moov atom not found" in media.error


def test_probe_timeout_is_safe(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="ffprobe",
            timeout=30,
        )

    monkeypatch.setattr(
        subprocess,
        "run",
        fake_run,
    )

    media = probe_media(
        "/media/movie.mkv"
    )

    assert media.probe_ok is False
    assert media.error is not None
    assert "timed out" in media.error


def test_probe_executes_read_only_ffprobe(monkeypatch):
    payload = {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
            },
        ],
        "format": {
            "duration": "100.0",
        },
    }

    seen = {}

    class Result:
        returncode = 0
        stdout = json.dumps(payload)
        stderr = ""

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["kwargs"] = kwargs
        return Result()

    monkeypatch.setattr(
        subprocess,
        "run",
        fake_run,
    )

    media = probe_media(
        Path("/media/movie.mkv")
    )

    assert media.probe_ok is True
    assert seen["command"][0] == "ffprobe"
    assert "-of" in seen["command"]
    assert "json" in seen["command"]

    forbidden = {
        "-i",
        "-y",
        "-c",
        "-codec",
    }

    assert forbidden.isdisjoint(
        set(seen["command"])
    )
