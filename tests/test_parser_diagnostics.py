from pathlib import Path

from deckflix_app.media import MediaInfo
from deckflix_app.screens.parser_diagnostics import (
    build_parser_diagnostic_report,
    diagnose_media,
)


def make_media(
    path: Path,
    *,
    title: str,
    media_type: str = "tv",
    season: int | None = 1,
    episode: int | None = 1,
) -> MediaInfo:
    return MediaInfo(
        path=path,
        media_type=media_type,
        title=title,
        year=None,
        season=season,
        episode=episode,
        resolution="unknown",
        source="unknown",
        codec="unknown",
        quality_score=0,
    )


def test_diagnostics_flags_generic_shuttle_title(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"

    diagnostic = diagnose_media(
        make_media(
            shuttle / "show.mkv",
            title="shuttle",
        ),
        shuttle,
    )

    assert diagnostic.needs_review
    assert any(
        "generic" in issue.lower()
        for issue in diagnostic.issues
    )


def test_diagnostics_flags_release_metadata(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"

    diagnostic = diagnose_media(
        make_media(
            shuttle / "show.mkv",
            title="Example Show S01E02 HDTV XviD",
            season=1,
            episode=2,
        ),
        shuttle,
    )

    assert diagnostic.needs_review
    assert any(
        "episode code" in issue.lower()
        for issue in diagnostic.issues
    )
    assert any(
        "release metadata" in issue.lower()
        for issue in diagnostic.issues
    )


def test_clean_title_passes_diagnostics(
    tmp_path: Path,
):
    shuttle = tmp_path / "shuttle"

    diagnostic = diagnose_media(
        make_media(
            shuttle / "show.mkv",
            title="Example Show",
        ),
        shuttle,
    )

    assert diagnostic.needs_review is False
    assert diagnostic.issues == []


def test_report_scans_real_files(tmp_path: Path):
    shuttle = tmp_path / "shuttle"
    show = shuttle / "Example Show" / "Season 01"

    show.mkdir(parents=True)
    (show / "Example.Show.S01E01.1080p.mkv").touch()

    report = build_parser_diagnostic_report(shuttle)

    assert report.total == 1
    assert report.clean + report.needs_review == 1
