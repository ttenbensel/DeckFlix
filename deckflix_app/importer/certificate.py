from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .results import ImportResult
from .safety import ShuttleSafetyResult


@dataclass(slots=True)
class ShuttleCertificate:
    shuttle_path: Path
    import_result: ImportResult
    safety: ShuttleSafetyResult
    created_at: datetime

    @property
    def trust_score(self) -> int:
        if self.safety.safe:
            return 100

        checks = 5
        failures = min(
            len(self.safety.reasons),
            checks,
        )

        return max(
            0,
            int(
                (
                    (checks - failures)
                    / checks
                )
                * 100
            ),
        )


def print_certificate(
    certificate: ShuttleCertificate,
) -> None:
    result = certificate.import_result
    safety = certificate.safety

    print()
    print(
        "══════════════════════════════════════════════"
    )
    print(
        "         DECKFLIX SHUTTLE CERTIFICATE"
    )
    print(
        "══════════════════════════════════════════════"
    )
    print()
    print(
        f"Shuttle        : "
        f"{certificate.shuttle_path}"
    )
    print(
        "Created        : "
        f"{certificate.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print()
    print("Import Summary")
    print("──────────────")
    print(
        f"Processed      : {result.total}"
    )
    print(
        f"Completed      : {result.completed}"
    )
    print(
        f"Failed         : {result.failed}"
    )

    print()
    print("Final Destination Audit")
    print("───────────────────────")
    print(
        f"SHA-256        : "
        f"{safety.audited_files}/"
        f"{safety.total_files}"
    )
    print(
        f"Audit Status   : "
        f"{'PASS' if safety.audit_complete else 'FAIL'}"
    )

    if safety.snapshot_coverage_required:
        print()
        print("Shuttle Snapshot Coverage")
        print("─────────────────────────")
        print(
            f"Snapshot files : "
            f"{safety.snapshot_files}"
        )
        print(
            f"Accounted      : "
            f"{safety.snapshot_accounted}"
        )
        print(
            f"Unresolved     : "
            f"{safety.snapshot_unresolved}"
        )
        print(
            f"Coverage       : "
            f"{safety.snapshot_coverage_percent}%"
        )

        print()
        print("Disposition")
        print("───────────")
        print(
            f"Imported       : "
            f"{safety.snapshot_imported}"
        )
        print(
            f"Identical      : "
            f"{safety.snapshot_identical}"
        )
        print(
            f"Superseded     : "
            f"{safety.snapshot_superseded}"
        )
        print(
            f"Review Hold    : "
            f"{safety.snapshot_review_hold}"
        )

        print()
        print(
            f"Coverage Status: "
            f"{'PASS' if safety.snapshot_coverage_complete else 'FAIL'}"
        )

    print()
    print(
        f"Trust Score    : "
        f"{certificate.trust_score}%"
    )

    print()
    print("Status")
    print("──────")
    print(
        safety.status
    )

    if safety.reasons:
        print()
        print("Reasons")
        print("───────")

        for reason in safety.reasons:
            print(
                f"- {reason}"
            )

    print()
    print(
        "══════════════════════════════════════════════"
    )
