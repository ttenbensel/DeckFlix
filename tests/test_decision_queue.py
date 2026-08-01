from pathlib import Path

from deckflix_app.decision import (
    Action,
    build_decision_queue,
    metadata_from_media_info,
)
from deckflix_app.media import MediaInfo
from deckflix_app.metadata.models import MediaMetadata


def movie(
    title: str,
    year: int,
    resolution: str,
) -> MediaMetadata:
    return MediaMetadata(
        media_type="movie",
        title=title,
        year=year,
        resolution=resolution,
        source="BluRay",
        video_codec="HEVC",
    )


def episode(
    title: str,
    season: int,
    episode_number: int,
    resolution: str,
) -> MediaMetadata:
    return MediaMetadata(
        media_type="tv",
        title=title,
        season=season,
        episode=episode_number,
        resolution=resolution,
        source="WEB-DL",
        video_codec="HEVC",
    )


def test_queue_marks_new_media():
    queue = build_decision_queue(
        incoming=[
            movie("Alien", 1979, "1080p"),
        ],
        library=[],
    )

    assert queue.total == 1
    assert queue.items[0].decision.action is Action.NEW


def test_queue_matches_tv_episode():
    queue = build_decision_queue(
        incoming=[
            episode("1883", 1, 1, "1080p"),
        ],
        library=[
            episode("1883", 1, 1, "720p"),
        ],
    )

    item = queue.items[0]

    assert item.existing is not None
    assert item.decision.action is Action.UPGRADE


def test_queue_does_not_match_different_episode():
    queue = build_decision_queue(
        incoming=[
            episode("1883", 1, 2, "1080p"),
        ],
        library=[
            episode("1883", 1, 1, "1080p"),
        ],
    )

    assert queue.items[0].decision.action is Action.NEW


def test_media_info_conversion(tmp_path: Path):
    file = tmp_path / "movie.mkv"
    file.write_bytes(b"media")

    info = MediaInfo(
        path=file,
        media_type="movie",
        title="Alien",
        year=1979,
        season=None,
        episode=None,
        resolution="1080p",
        source="BluRay",
        codec="HEVC",
        quality_score=0,
    )

    metadata = metadata_from_media_info(info)

    assert metadata.title == "Alien"
    assert metadata.year == 1979
    assert metadata.path == file
    assert metadata.size == 5
    assert metadata.video_codec == "HEVC"


def test_queue_summary():
    queue = build_decision_queue(
        incoming=[
            movie("Alien", 1979, "1080p"),
            movie("Avatar", 2009, "1080p"),
        ],
        library=[
            movie("Avatar", 2009, "1080p"),
        ],
    )

    summary = queue.summary()

    assert summary[Action.NEW] == 1
    assert summary[Action.DUPLICATE] == 1
