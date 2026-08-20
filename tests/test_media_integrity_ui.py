from pathlib import Path
from types import SimpleNamespace

import deckflix_app.library_health as ui
from deckflix_app.library.integrity import (
    MediaIntegrityResult,
    MediaIntegrityStatus,
)
from deckflix_app.metadata.models import MediaMetadata


def _entry(
    path: str,
    title: str,
):
    return SimpleNamespace(
        media=MediaMetadata(
            media_type="movie",
            content_type="movie",
            title=title,
            path=Path(path),
        )
    )


def test_media_integrity_screen_is_simple_and_read_only(
    monkeypatch,
    capsys,
):
    audit = SimpleNamespace(
        entries=[
            _entry(
                "/media/good.mkv",
                "Good",
            ),
            _entry(
                "/media/bad.mkv",
                "Bad",
            ),
        ]
    )

    monkeypatch.setattr(
        ui,
        "probe_media",
        lambda path: object(),
    )

    def classify(
        media,
        technical,
    ):
        if media.title == "Good":
            return MediaIntegrityResult(
                status=(
                    MediaIntegrityStatus.HEALTHY
                ),
                reasons=(
                    "Playable media passed "
                    "integrity checks.",
                ),
            )

        return MediaIntegrityResult(
            status=MediaIntegrityStatus.CORRUPT,
            reasons=(
                "Media file is zero bytes.",
            ),
        )

    monkeypatch.setattr(
        ui,
        "classify_media_integrity",
        classify,
    )

    ui._show_media_integrity(audit)

    output = capsys.readouterr().out

    assert "Media Integrity" in output
    assert "Healthy          1" in output
    assert "Bad Media        1" in output
    assert "Bad" in output
    assert "/media/bad.mkv" in output
    assert "Media file is zero bytes." in output
    assert "READ-ONLY" in output
    assert "No files have been changed." in output


def test_library_health_opens_media_integrity(
    monkeypatch,
):
    audit = SimpleNamespace(
        entries=[],
        duplicate_groups={},
        summary=SimpleNamespace(
            total_files=0,
            total_bytes=0,
            correct=0,
            misplaced=0,
            legacy=0,
            duplicate_candidates=0,
            structure_review=0,
            weak_metadata=0,
        ),
    )

    called = []

    monkeypatch.setattr(
        ui,
        "audit_libraries",
        lambda roots: audit,
    )
    monkeypatch.setattr(
        ui,
        "current_deckflix_library_roots",
        lambda: [],
    )
    monkeypatch.setattr(
        ui,
        "_show_summary",
        lambda audit: None,
    )
    monkeypatch.setattr(
        ui,
        "_show_media_integrity",
        lambda audit: called.append(audit),
    )

    answers = iter(
        [
            "6",
            "",
            "8",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    ui.show_library_health()

    assert called == [audit]
