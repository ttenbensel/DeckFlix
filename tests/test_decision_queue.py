from pathlib import Path

from deckflix_app.decision.queue import (
    _deduplicate_incoming,
)

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


def test_incoming_duplicate_tv_episode_is_collapsed():
    first = episode(
        "South Park",
        26,
        2,
        "720p",
    )

    second = episode(
        "South Park",
        26,
        2,
        "1080p",
    )

    queue = build_decision_queue(
        incoming=[
            first,
            second,
        ],
        library=[],
    )

    assert queue.total == 1
    assert queue.items[0].incoming is second
    assert queue.items[0].decision.action is Action.NEW


def test_incoming_duplicate_tv_episode_keeps_highest_quality():
    low_quality = episode(
        "South Park",
        26,
        2,
        "720p",
    )

    high_quality = episode(
        "South Park",
        26,
        2,
        "1080p",
    )

    queue = build_decision_queue(
        incoming=[
            high_quality,
            low_quality,
        ],
        library=[],
    )

    assert queue.total == 1
    assert queue.items[0].incoming is high_quality
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


def test_metadata_queue_does_not_probe(monkeypatch):
    import deckflix_app.decision.queue as queue_module

    def forbidden_probe(path):
        raise AssertionError(
            f"pure metadata queue probed {path}"
        )

    monkeypatch.setattr(
        queue_module,
        "probe_media",
        forbidden_probe,
    )

    queue = build_decision_queue(
        incoming=[
            movie("Avatar", 2009, "1080p"),
        ],
        library=[
            movie("Avatar", 2009, "720p"),
        ],
    )

    assert (
        queue.items[0].decision.action
        is Action.UPGRADE
    )


def test_path_queue_uses_verified_quality(
    tmp_path: Path,
    monkeypatch,
):
    from deckflix_app.decision import (
        build_decision_queue_from_paths,
    )
    from deckflix_app.metadata.technical import (
        TechnicalMetadata,
        VideoStreamMetadata,
    )

    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    incoming_file = (
        shuttle
        / "Avatar (2009) 720p BluRay HEVC.mkv"
    )
    existing_file = (
        movies
        / "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    incoming_file.write_bytes(b"incoming")
    existing_file.write_bytes(b"existing")

    def fake_probe(path):
        path = Path(path)

        if path == incoming_file:
            return TechnicalMetadata(
                path=path,
                probe_ok=True,
                primary_video=VideoStreamMetadata(
                    index=0,
                    width=3840,
                    height=2160,
                    codec="hevc",
                ),
            )

        if path == existing_file:
            return TechnicalMetadata(
                path=path,
                probe_ok=True,
                primary_video=VideoStreamMetadata(
                    index=0,
                    width=1920,
                    height=1080,
                    codec="hevc",
                ),
            )

        raise AssertionError(
            f"unexpected probe path: {path}"
        )

    monkeypatch.setattr(
        "deckflix_app.decision.queue.probe_media",
        fake_probe,
    )

    queue = build_decision_queue_from_paths(
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
    )

    assert queue.total == 1
    assert (
        queue.items[0].decision.action
        is Action.UPGRADE
    )


def test_path_queue_failed_probe_falls_back(
    tmp_path: Path,
    monkeypatch,
):
    from deckflix_app.decision import (
        build_decision_queue_from_paths,
    )
    from deckflix_app.metadata.technical import (
        TechnicalMetadata,
    )

    shuttle = tmp_path / "shuttle"
    movies = tmp_path / "movies"
    tv = tmp_path / "tv"

    shuttle.mkdir()
    movies.mkdir()
    tv.mkdir()

    incoming_file = (
        shuttle
        / "Avatar (2009) 720p BluRay HEVC.mkv"
    )
    existing_file = (
        movies
        / "Avatar (2009) 1080p BluRay HEVC.mkv"
    )

    incoming_file.write_bytes(b"incoming")
    existing_file.write_bytes(b"existing")

    def failed_probe(path):
        return TechnicalMetadata(
            path=Path(path),
            probe_ok=False,
            error="test probe failure",
        )

    monkeypatch.setattr(
        "deckflix_app.decision.queue.probe_media",
        failed_probe,
    )

    queue = build_decision_queue_from_paths(
        shuttle_path=shuttle,
        movie_libraries=[movies],
        tv_libraries=[tv],
    )

    assert queue.total == 1
    assert (
        queue.items[0].decision.action
        is Action.DOWNGRADE
    )


def test_verified_queue_probes_same_path_once(
    tmp_path: Path,
    monkeypatch,
):
    """
    A real file encountered more than once during one verified
    queue build must be ffprobed only once.
    """
    import deckflix_app.decision.queue as queue_module

    from deckflix_app.metadata.technical import (
        TechnicalMetadata,
        VideoStreamMetadata,
    )

    shared_file = tmp_path / "Avatar (2009) 1080p BluRay HEVC.mkv"
    shared_file.write_bytes(b"media")

    incoming = MediaMetadata(
        media_type="movie",
        title="Avatar",
        year=2009,
        resolution="1080p",
        source="BluRay",
        video_codec="HEVC",
        path=shared_file,
    )

    existing = MediaMetadata(
        media_type="movie",
        title="Avatar",
        year=2009,
        resolution="1080p",
        source="BluRay",
        video_codec="HEVC",
        path=shared_file,
    )

    calls = []

    def fake_probe(path):
        path = Path(path)
        calls.append(path)

        return TechnicalMetadata(
            path=path,
            probe_ok=True,
            primary_video=VideoStreamMetadata(
                index=0,
                width=1920,
                height=1080,
                codec="hevc",
            ),
        )

    monkeypatch.setattr(
        queue_module,
        "probe_media",
        fake_probe,
    )

    queue = queue_module._build_verified_decision_queue(
        incoming=[incoming],
        library=[existing],
    )

    assert queue.total == 1
    assert len(calls) == 1
    assert calls[0] == shared_file.resolve()


def test_verified_queue_caches_failed_probe(
    tmp_path: Path,
    monkeypatch,
):
    """
    Failed probe results are also cached for the lifetime of a
    queue build so the same broken/unprobeable file is not retried.
    """
    import deckflix_app.decision.queue as queue_module

    from deckflix_app.metadata.technical import (
        TechnicalMetadata,
    )

    shared_file = tmp_path / "Avatar (2009) 1080p BluRay HEVC.mkv"
    shared_file.write_bytes(b"media")

    incoming = MediaMetadata(
        media_type="movie",
        title="Avatar",
        year=2009,
        resolution="1080p",
        source="BluRay",
        video_codec="HEVC",
        path=shared_file,
    )

    existing = MediaMetadata(
        media_type="movie",
        title="Avatar",
        year=2009,
        resolution="1080p",
        source="BluRay",
        video_codec="HEVC",
        path=shared_file,
    )

    calls = []

    def failed_probe(path):
        path = Path(path)
        calls.append(path)

        return TechnicalMetadata(
            path=path,
            probe_ok=False,
            error="test probe failure",
        )

    monkeypatch.setattr(
        queue_module,
        "probe_media",
        failed_probe,
    )

    queue = queue_module._build_verified_decision_queue(
        incoming=[incoming],
        library=[existing],
    )

    assert queue.total == 1
    assert len(calls) == 1
    assert calls[0] == shared_file.resolve()


def test_verified_queue_does_not_probe_new_media(
    tmp_path: Path,
    monkeypatch,
):
    """
    Technical quality cannot affect a NEW decision, so a media file
    with no matching library item must not be ffprobed.
    """
    import deckflix_app.decision.queue as queue_module

    incoming_file = (
        tmp_path
        / "Alien (1979) 1080p BluRay HEVC.mkv"
    )
    incoming_file.write_bytes(
        b"new media"
    )

    incoming = MediaMetadata(
        media_type="movie",
        title="Alien",
        year=1979,
        resolution="1080p",
        source="BluRay",
        video_codec="HEVC",
        path=incoming_file,
    )

    calls = []

    def forbidden_probe(path):
        calls.append(
            Path(path)
        )

        raise AssertionError(
            "NEW media must not be technically probed"
        )

    monkeypatch.setattr(
        queue_module,
        "probe_media",
        forbidden_probe,
    )

    queue = (
        queue_module
        ._build_verified_decision_queue(
            incoming=[
                incoming,
            ],
            library=[],
        )
    )

    assert queue.total == 1
    assert (
        queue.items[0].decision.action
        is Action.NEW
    )
    assert calls == []


def test_verified_queue_still_probes_existing_match(
    tmp_path: Path,
    monkeypatch,
):
    """
    Existing-media comparisons still require technical verification.
    """
    import deckflix_app.decision.queue as queue_module

    from deckflix_app.metadata.technical import (
        TechnicalMetadata,
        VideoStreamMetadata,
    )

    incoming_file = (
        tmp_path
        / "Avatar (2009) 720p BluRay HEVC.mkv"
    )
    existing_file = (
        tmp_path
        / "Avatar (2009) 1080p BluRay HEVC existing.mkv"
    )

    incoming_file.write_bytes(
        b"incoming"
    )
    existing_file.write_bytes(
        b"existing"
    )

    incoming = MediaMetadata(
        media_type="movie",
        title="Avatar",
        year=2009,
        resolution="720p",
        source="BluRay",
        video_codec="HEVC",
        path=incoming_file,
    )

    existing = MediaMetadata(
        media_type="movie",
        title="Avatar",
        year=2009,
        resolution="1080p",
        source="BluRay",
        video_codec="HEVC",
        path=existing_file,
    )

    calls = []

    def fake_probe(path):
        resolved = Path(path).resolve()
        calls.append(
            resolved
        )

        width = (
            3840
            if resolved
            == incoming_file.resolve()
            else 1920
        )

        height = (
            2160
            if resolved
            == incoming_file.resolve()
            else 1080
        )

        return TechnicalMetadata(
            path=resolved,
            probe_ok=True,
            primary_video=VideoStreamMetadata(
                index=0,
                width=width,
                height=height,
                codec="hevc",
            ),
        )

    monkeypatch.setattr(
        queue_module,
        "probe_media",
        fake_probe,
    )

    queue = (
        queue_module
        ._build_verified_decision_queue(
            incoming=[
                incoming,
            ],
            library=[
                existing,
            ],
        )
    )

    assert queue.total == 1

    assert (
        queue.items[0].decision.action
        is Action.UPGRADE
    )

    assert sorted(calls) == sorted(
        [
            incoming_file.resolve(),
            existing_file.resolve(),
        ]
    )


def test_incoming_tv_items_without_episode_identity_are_not_deduplicated():
    first = MediaMetadata(
        media_type="tv",
        title="Rick and Morty",
        content_type="extra",
        season=None,
        episode=None,
        path=Path(
            "/shuttle/Rick and Morty/Extras/"
            "Behind The Scenes.mkv"
        ),
    )

    second = MediaMetadata(
        media_type="tv",
        title="Rick and Morty",
        content_type="extra",
        season=None,
        episode=None,
        path=Path(
            "/shuttle/Rick and Morty/Extras/"
            "Deleted Scene.mkv"
        ),
    )

    result = _deduplicate_incoming(
        [first, second]
    )

    assert len(result) == 2
    assert first in result
    assert second in result


def test_incoming_specials_without_episode_identity_are_not_deduplicated():
    first = MediaMetadata(
        media_type="tv",
        title="South Park",
        content_type="special",
        season=None,
        episode=None,
        path=Path(
            "/shuttle/South Park/Specials/"
            "Pandemic Special.mkv"
        ),
    )

    second = MediaMetadata(
        media_type="tv",
        title="South Park",
        content_type="special",
        season=None,
        episode=None,
        path=Path(
            "/shuttle/South Park/Specials/"
            "Post Covid.mkv"
        ),
    )

    result = _deduplicate_incoming(
        [first, second]
    )

    assert len(result) == 2
    assert first in result
    assert second in result


def test_normal_tv_episode_deduplication_is_preserved():
    lower = MediaMetadata(
        media_type="tv",
        title="South Park",
        content_type="episode",
        season=26,
        episode=2,
        resolution="720p",
        source="HDTV",
        video_codec="H264",
        path=Path(
            "/shuttle/South Park/"
            "South.Park.S26E02.720p.HDTV.mkv"
        ),
    )

    higher = MediaMetadata(
        media_type="tv",
        title="South Park",
        content_type="episode",
        season=26,
        episode=2,
        resolution="1080p",
        source="WEB-DL",
        video_codec="H264",
        path=Path(
            "/shuttle/South Park/"
            "South.Park.S26E02.1080p.WEB-DL.mkv"
        ),
    )

    result = _deduplicate_incoming(
        [lower, higher]
    )

    assert len(result) == 1
    assert result[0] is higher
