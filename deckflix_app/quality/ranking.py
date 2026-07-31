from deckflix_app.metadata.models import MediaMetadata

RESOLUTION = {
    "2160p": 4,
    "1080p": 3,
    "720p": 2,
    "480p": 1,
}

SOURCE = {
    "remux": 6,
    "bluray": 5,
    "web-dl": 4,
    "webrip": 3,
    "web": 2,
    "dvd": 1,
}

CODEC = {
    "hevc": 2,
    "x265": 2,
    "h265": 2,
    "x264": 1,
    "h264": 1,
}


def quality_score(media: MediaMetadata) -> int:
    resolution = RESOLUTION.get(
        (media.resolution or "").lower(),
        0,
    )

    source = SOURCE.get(
        (media.source or "").lower(),
        0,
    )

    codec = CODEC.get(
        (media.video_codec or "").lower(),
        0,
    )

    return resolution * 100 + source * 10 + codec
