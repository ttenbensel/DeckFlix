from pathlib import Path


def print_maintenance_certificate(
    journal,
):
    verified = sum(
        1
        for entry in journal.entries
        if entry.status.value == "VERIFIED"
    )

    failed = sum(
        1
        for entry in journal.entries
        if entry.status.value == "FAILED"
    )

    print()
    print("DECKFLIX MAINTENANCE CERTIFICATE")
    print("═══════════════════════════════")
    print()

    print(
        f"Actions   : {len(journal.entries)}"
    )
    print(
        f"Verified  : {verified}"
    )
    print(
        f"Failed    : {failed}"
    )
    print()

    if failed == 0:
        print(
            "Integrity : VALID"
        )
        print(
            "Result    : COMPLETE"
        )
    else:
        print(
            "Integrity : REVIEW REQUIRED"
        )
        print(
            "Result    : FAILED"
        )

    print()
    print(
        f"Journal   : {journal.path}"
    )
