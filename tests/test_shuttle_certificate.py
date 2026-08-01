from datetime import datetime
from pathlib import Path

from deckflix_app.importer import (
    ImportResult,
    ShuttleCertificate,
    ShuttleSafetyResult,
)


def test_safe_certificate_has_full_trust(tmp_path: Path):
    certificate = ShuttleCertificate(
        shuttle_path=tmp_path / "shuttle",
        import_result=ImportResult(
            total=2,
            completed=2,
            failed=0,
        ),
        safety=ShuttleSafetyResult(
            safe=True,
            reasons=[],
            audited_files=2,
            total_files=2,
        ),
        created_at=datetime(2026, 8, 1, 12, 0, 0),
    )

    assert certificate.trust_score == 100


def test_unsafe_certificate_reduces_trust(tmp_path: Path):
    certificate = ShuttleCertificate(
        shuttle_path=tmp_path / "shuttle",
        import_result=ImportResult(
            total=2,
            completed=1,
            failed=1,
        ),
        safety=ShuttleSafetyResult(
            safe=False,
            reasons=[
                "One import failed",
                "One job remains pending",
            ],
            audited_files=1,
            total_files=2,
        ),
        created_at=datetime(2026, 8, 1, 12, 0, 0),
    )

    assert certificate.trust_score == 60
